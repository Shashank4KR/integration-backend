import logging
import smtplib
import secrets
from email.message import EmailMessage
from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.refresh_token_model import RefreshToken
from app.models.password_reset import PasswordReset
from app.models.user import User
from app.schemas.auth_schema import (
    MFASetupResponse,
    MFAVerifyRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from app.schemas.settings_schema import ChangePasswordRequest, ForgotPasswordRequest, ResetPasswordRequest, ProfileUpdateRequest
from app.schemas.user import UserCreate, UserCreateResponse, UserResponse
from app.services.audit_service import audit_log_service, login_history_service
from app.services.auth_service import AuthService
from app.services.role_resolver import resolve_role
from app.services.totp_service import TOTPService

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

router = APIRouter()

def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _validate_new_password(password: str) -> None:
    if len(password) < 12 or not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        raise HTTPException(status_code=400, detail="Password must be at least 12 characters and include a letter and a number")


def _send_reset_email(email: str, url: str) -> None:
    message = EmailMessage()
    message["Subject"] = "Reset your Nomera password"
    message["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME or ""
    message["To"] = email
    message.set_content(f"Use this link within 30 minutes to reset your password:\n\n{url}\n\nIf you did not request this, ignore this email.")
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls()
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(message)


def _deliver_reset_email(email: str, url: str) -> None:
    try:
        _send_reset_email(email, url)
    except Exception:
        logger.exception("Password reset email delivery failed")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = AuthService.verify_token(token)
    if payload is None:
        raise credentials_exception

    if payload.get("type", "access") != "access":
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    if user.username == "demo-superadmin" and not settings.demo_superadmin_active:
        raise credentials_exception

    # Check token version to enforce revocation on logout / password change
    token_ver = payload.get("ver")
    if token_ver is not None and hasattr(user, "token_version") and user.token_version is not None:
        if token_ver != user.token_version:
            raise credentials_exception

    role_name = (user.role.role_name if user.role else "").upper()
    if role_name != "ADMIN":
        try:
            from app.services.settings_service import settings_service

            system_settings = await settings_service.get_category_settings(db, "system")
            if bool(system_settings.get("maintenance_mode", False)):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="System is currently in maintenance mode. Please try again later.",
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Error checking maintenance mode in get_current_user: {e}")

    return user


@router.post("/register", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserCreateResponse:
    role_name = (current_user.role.role_name if current_user.role else "").upper()
    if role_name != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create users",
        )

    email_result = await db.execute(select(User).where(User.email == user_in.email))
    if email_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    username_result = await db.execute(
        select(User).where(User.username == user_in.username)
    )
    if username_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered",
        )

    role = await resolve_role(db, user_in.role_id)

    hashed_password = AuthService.hash_password(user_in.password)
    new_user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=hashed_password,
        phone=user_in.phone,
        status=user_in.status,
        role_id=role.id,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    response = UserCreateResponse.model_validate(new_user)
    response.created_id = new_user.id
    return response


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> dict:
    result = await db.execute(
        select(User).where(
            or_(User.email == form_data.username, User.username == form_data.username)
        )
    )
    user = result.scalar_one_or_none()

    if user and user.username == "demo-superadmin" and not settings.demo_superadmin_active:
        user = None

    # Check per-account lockout
    if user and user.locked_until:
        now_utc = datetime.now(UTC)
        if _ensure_utc(user.locked_until) > now_utc:
            remaining_mins = max(1, int((user.locked_until - now_utc).total_seconds() // 60) + 1)
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account is temporarily locked due to repeated failed logins. Please try again in {remaining_mins} minutes.",
            )

    if user is None or not AuthService.verify_password(
        form_data.password, user.password_hash
    ):
        if user:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.now(UTC) + timedelta(minutes=15)
                logger.warning(f"User account '{user.username}' locked due to 5 consecutive failed login attempts.")
            db.add(user)
            await db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    user_role_name = (user.role.role_name if user.role else "").upper()

    # MFA enforcement when enabled via config flag
    if settings.ENABLE_MFA and user_role_name in {"ADMIN", "SUPERADMIN", "ACCOUNTANT"}:
        if user.mfa_enabled:
            mfa_code = (
                request.headers.get("X-MFA-Code") or request.headers.get("X-TOTP-Code")
                if request
                else None
            )
            if not mfa_code:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="MFA code required for privileged role. Provide via X-MFA-Code header.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            if not TOTPService.verify_totp(user.mfa_secret or "", mfa_code):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid MFA code",
                    headers={"WWW-Authenticate": "Bearer"},
                )


    # Check maintenance mode (admin is ALWAYS allowed to login)
    if user_role_name != "ADMIN":
        try:
            from app.services.settings_service import settings_service

            system_settings = await settings_service.get_category_settings(db, "system")
            if bool(system_settings.get("maintenance_mode", False)):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="System is currently under maintenance. Only administrators can log in at this time.",
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Error checking maintenance mode in login: {e}")

    # Reset failed login count and lockout on successful authentication
    now_utc = datetime.now(UTC)
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = now_utc
    db.add(user)

    login_record = await login_history_service.create_login_record(
        db,
        {
            "user_id": user.id,
            "device": request.headers.get("user-agent") if request else None,
            "ip_address": request.client.host if request and request.client else None,
        },
        commit=False,
    )
    await audit_log_service.create_log(
        db,
        {"user_id": user.id, "activity": "User Login", "details": "Successful login"},
        commit=False,
    )

    access_token = AuthService.create_access_token(
        data={
            "sub": str(user.id),
            "sid": str(login_record.id),
            "ver": user.token_version or 1,
            "type": "access",
        },
        expires_delta=timedelta(minutes=AuthService.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    raw_refresh_token = AuthService.create_refresh_token()
    refresh_record = RefreshToken(
        user_id=user.id,
        token_hash=AuthService.hash_token(raw_refresh_token),
        expires_at=now_utc + timedelta(days=AuthService.REFRESH_TOKEN_EXPIRE_DAYS),
        revoked=False,
    )
    db.add(refresh_record)
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": raw_refresh_token,
        "token_type": "bearer",
        "must_change_password": bool(user.must_change_password),
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    now_utc = datetime.now(UTC)
    token_hash = AuthService.hash_token(payload.refresh_token)

    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    token_record = result.scalar_one_or_none()

    if token_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check for refresh token reuse
    if token_record.revoked:
        user_result = await db.execute(
            select(User).where(User.id == token_record.user_id)
        )
        user = user_result.scalar_one_or_none()
        if user:
            user.token_version = (user.token_version or 1) + 1
            db.add(user)
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == token_record.user_id)
            .values(revoked=True)
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token reuse detected. All sessions revoked.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if _ensure_utc(token_record.expires_at) < now_utc:
        token_record.revoked = True
        db.add(token_record)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Rotate refresh token: revoke used one and issue a new one
    token_record.revoked = True
    db.add(token_record)

    user_result = await db.execute(
        select(User).where(User.id == token_record.user_id)
    )
    user = user_result.scalar_one_or_none()
    if user is None or not user.status:
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    new_raw_refresh = AuthService.create_refresh_token()
    new_token_record = RefreshToken(
        user_id=user.id,
        token_hash=AuthService.hash_token(new_raw_refresh),
        expires_at=now_utc + timedelta(days=AuthService.REFRESH_TOKEN_EXPIRE_DAYS),
        revoked=False,
    )
    db.add(new_token_record)

    new_access_token = AuthService.create_access_token(
        data={
            "sub": str(user.id),
            "ver": user.token_version or 1,
            "type": "access",
        },
        expires_delta=timedelta(minutes=AuthService.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    await db.commit()

    return {
        "access_token": new_access_token,
        "refresh_token": new_raw_refresh,
        "token_type": "bearer",
        "must_change_password": bool(user.must_change_password),
    }


@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    payload = AuthService.verify_token(token) or {}
    session_id = payload.get("sid")
    if session_id:
        try:
            await login_history_service.update_logout_record(db, UUID(session_id), commit=False)
        except (ValueError, HTTPException) as e:
            logger.debug(f"Logout record update error: {e}")

    # Invalidate all active tokens for this user
    current_user.token_version = (current_user.token_version or 1) + 1
    db.add(current_user)

    # Revoke all active refresh tokens for this user
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == current_user.id)
        .values(revoked=True)
    )

    await audit_log_service.create_log(
        db,
        {
            "user_id": current_user.id,
            "activity": "User Logout",
            "details": "User logged out; active tokens invalidated",
        },
        commit=False,
    )
    await db.commit()
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    new_username = payload.username
    new_email = payload.email
    new_phone = payload.phone

    if new_username and new_username != current_user.username:
        result = await db.execute(
            select(User).where(User.username == new_username, User.id != current_user.id)
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username is already taken by another account",
            )
        current_user.username = new_username

    if new_email and new_email != current_user.email:
        result = await db.execute(
            select(User).where(User.email == new_email, User.id != current_user.id)
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email address is already in use by another account",
            )
        current_user.email = new_email

    if new_phone is not None:
        current_user.phone = new_phone

    if payload.avatar_url is not None:
        new_avatar = payload.avatar_url
        if not (new_avatar.startswith(("data:image/", "http://", "https://", "/"))):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Avatar must be a valid image URL or data URI",
            )
        current_user.avatar_url = new_avatar

    db.add(current_user)
    await audit_log_service.create_log(
        db,
        {
            "user_id": current_user.id,
            "activity": "Profile Updated",
            "details": "User updated personal profile details",
        },
        commit=False,
    )
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    current_password = payload.current_password
    new_password = payload.new_password

    if not AuthService.verify_password(current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    _validate_new_password(new_password)
    if AuthService.verify_password(new_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="New password must be different from your current password")
    if payload.confirm_password is not None and payload.confirm_password != new_password:
        raise HTTPException(status_code=400, detail="New password and confirmation do not match")

    current_user.password_hash = AuthService.hash_password(new_password)
    current_user.must_change_password = False
    current_user.password_changed_at = datetime.now(UTC)

    # Invalidate all existing tokens on password change
    current_user.token_version = (current_user.token_version or 1) + 1
    db.add(current_user)

    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == current_user.id)
        .values(revoked=True)
    )

    await audit_log_service.create_log(
        db,
        {
            "user_id": current_user.id,
            "activity": "Password Changed",
            "details": "User successfully changed their password; active sessions invalidated",
        },
        commit=False,
    )
    await db.commit()
    return {"message": "Password changed successfully"}


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, request: Request, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)) -> dict:
    generic = {"message": "If an account exists for that email, password reset instructions will be sent."}
    normalized_email = str(payload.email).strip().lower()
    result = await db.execute(select(User).where(User.email.ilike(normalized_email), User.status.is_(True)))
    user = result.scalar_one_or_none()
    # Without a delivery channel, don't create a token that cannot be delivered.
    if user is None or not (settings.SMTP_HOST and settings.SMTP_FROM_EMAIL):
        return generic
    raw_token = secrets.token_urlsafe(32)
    reset = PasswordReset(user_id=user.id, token_hash=AuthService.hash_token(raw_token), expires_at=datetime.now(UTC) + timedelta(minutes=30))
    await db.execute(update(PasswordReset).where(PasswordReset.user_id == user.id, PasswordReset.used_at.is_(None)).values(used_at=datetime.now(UTC)))
    db.add(reset)
    await db.commit()
    background_tasks.add_task(_deliver_reset_email, user.email, f"{settings.FRONTEND_BASE_URL.rstrip('/')}/reset-password#token={raw_token}")
    return generic


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)) -> dict:
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="New password and confirmation do not match")
    _validate_new_password(payload.new_password)
    now = datetime.now(UTC)
    token_hash = AuthService.hash_token(payload.token)
    result = await db.execute(select(PasswordReset).where(PasswordReset.token_hash == token_hash).with_for_update())
    reset = result.scalar_one_or_none()
    if reset is None or reset.used_at is not None or _ensure_utc(reset.expires_at) <= now:
        raise HTTPException(status_code=400, detail="Reset link is invalid or expired. Request a new one.")
    user = await db.get(User, reset.user_id)
    if user is None or not user.status:
        raise HTTPException(status_code=400, detail="Reset link is invalid or expired. Request a new one.")
    if AuthService.verify_password(payload.new_password, user.password_hash):
        raise HTTPException(status_code=400, detail="New password must be different from your current password")
    user.password_hash = AuthService.hash_password(payload.new_password)
    user.password_changed_at = now
    user.must_change_password = False
    user.token_version = (user.token_version or 1) + 1
    reset.used_at = now
    await db.execute(update(PasswordReset).where(PasswordReset.user_id == user.id, PasswordReset.id != reset.id, PasswordReset.used_at.is_(None)).values(used_at=now))
    await db.execute(update(RefreshToken).where(RefreshToken.user_id == user.id).values(revoked=True))
    await db.commit()
    return {"message": "Password reset successfully. Please sign in with your new password."}


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    secret = TOTPService.generate_secret()
    current_user.mfa_secret = secret
    current_user.mfa_enabled = False
    db.add(current_user)
    await db.commit()
    otpauth_uri = TOTPService.get_provisioning_uri(
        current_user.username or current_user.email, secret
    )
    return {
        "secret": secret,
        "otpauth_uri": otpauth_uri,
    }


@router.post("/mfa/enable")
async def enable_mfa(
    payload: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if not current_user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not set up. Call /auth/mfa/setup first.",
        )
    if not TOTPService.verify_totp(current_user.mfa_secret, payload.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MFA verification code.",
        )
    current_user.mfa_enabled = True
    db.add(current_user)
    await db.commit()
    return {"message": "MFA enabled successfully"}


@router.post("/mfa/disable")
async def disable_mfa(
    payload: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if not current_user.mfa_enabled or not current_user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not currently enabled.",
        )
    if not TOTPService.verify_totp(current_user.mfa_secret, payload.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MFA verification code.",
        )
    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    db.add(current_user)
    await db.commit()
    return {"message": "MFA disabled successfully"}


@router.get("/sessions")
async def get_my_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    history = await login_history_service.get_user_history(db, current_user.id)
    return [
        {
            "id": str(record.id),
            "login_time": record.login_time.isoformat() if record.login_time else None,
            "logout_time": record.logout_time.isoformat() if record.logout_time else None,
            "device": record.device or "Browser on Desktop",
            "ip_address": record.ip_address or "127.0.0.1",
            "is_active": record.logout_time is None,
        }
        for record in history[:10]
    ]
