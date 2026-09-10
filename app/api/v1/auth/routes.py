from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.role_resolver import resolve_role
from app.services.auth_service import AuthService
from app.schemas.user import UserCreate, UserCreateResponse, UserResponse
from app.models.user import User
from app.services.audit_service import audit_log_service, login_history_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

router = APIRouter()


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
        except Exception:
            pass

    return user


@router.post("/register", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserCreateResponse:
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

    if user is None or not AuthService.verify_password(
        form_data.password, user.password_hash
    ):
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

    # Check maintenance mode (admin is ALWAYS allowed to login)
    user_role_name = (user.role.role_name if user.role else "").upper()
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
        except Exception:
            pass

    login_record = await login_history_service.create_login_record(db, {
        "user_id": user.id,
        "device": request.headers.get("user-agent") if request else None,
        "ip_address": request.client.host if request and request.client else None,
    }, commit=False)
    await audit_log_service.create_log(db, {
        "user_id": user.id, "activity": "User Login", "details": "Successful login"
    }, commit=False)
    await db.commit()

    access_token = AuthService.create_access_token(
        data={"sub": str(user.id), "sid": str(login_record.id)},
        expires_delta=timedelta(minutes=AuthService.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {"access_token": access_token, "token_type": "bearer"}


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
        except (ValueError, HTTPException):
            pass
    await audit_log_service.create_log(db, {"user_id": current_user.id, "activity": "User Logout", "details": "User logged out"}, commit=False)
    await db.commit()
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    new_username = payload.get("username")
    new_email = payload.get("email")
    new_phone = payload.get("phone")

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

    if "avatar_url" in payload:
        current_user.avatar_url = payload.get("avatar_url")

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
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    current_password = payload.get("current_password")
    new_password = payload.get("new_password")

    if not current_password or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password and new password are required",
        )

    if not AuthService.verify_password(current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    if len(new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters long",
        )

    current_user.password_hash = AuthService.hash_password(new_password)
    db.add(current_user)
    await audit_log_service.create_log(
        db,
        {
            "user_id": current_user.id,
            "activity": "Password Changed",
            "details": "User successfully changed their password",
        },
        commit=False,
    )
    await db.commit()
    return {"message": "Password changed successfully"}


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

