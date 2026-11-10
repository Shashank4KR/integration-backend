from sqlalchemy import func, select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.role import Role
from app.models.user import User
from app.services.auth_service import AuthService


async def ensure_demo_superadmin() -> None:
    """Create a local demo account only when explicitly enabled for development."""
    if not settings.ENABLE_DEMO_SUPERADMIN:
        return
    if not settings.demo_superadmin_active:
        raise RuntimeError("Demo superadmin is only allowed in development or local environments.")

    email = (settings.DEMO_SUPERADMIN_EMAIL or "").strip().lower()
    password = settings.DEMO_SUPERADMIN_PASSWORD or ""
    if not email or len(password) < 12:
        raise RuntimeError("Demo superadmin requires an email and a password of at least 12 characters.")

    async with AsyncSessionLocal() as session:
        role = await session.scalar(select(Role).where(func.upper(Role.role_name) == "SUPER_ADMIN"))
        if role is None:
            raise RuntimeError("SUPER_ADMIN role is missing. Apply the database migrations first.")

        existing_email_user = await session.scalar(select(User).where(func.lower(User.email) == email))
        if existing_email_user is not None:
            existing_role = (existing_email_user.role.role_name if existing_email_user.role else "").upper()
            if existing_role in {"SUPER_ADMIN", "SUPERADMIN"}:
                return
            raise RuntimeError("Configured demo email already belongs to a non-superadmin account.")

        username = "demo-superadmin"
        username_in_use = await session.scalar(select(User.id).where(User.username == username))
        if username_in_use is not None:
            raise RuntimeError("Demo username is already in use. Resolve it before enabling demo access.")

        session.add(
            User(
                username=username,
                email=email,
                password_hash=AuthService.hash_password(password),
                status=True,
                role_id=role.id,
            )
        )
        await session.commit()
