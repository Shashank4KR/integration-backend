from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role


ROLE_CODE_TO_NAME = {
    "0001": "ADMIN",
    "0002": "TEACHER",
    "0003": "PARENT",
    "0004": "STUDENT",
    "0005": "ACCOUNTANT",
    "0006": "LIBRARIAN",
    "0007": "WARDEN",
    "0008": "SUPER_ADMIN",
}


def role_uuid_from_code(role_code: str) -> UUID:
    return UUID(f"00000000-0000-0000-0000-{int(role_code):012d}")


async def resolve_role(session: AsyncSession, public_role_id: str) -> Role:
    role_key = public_role_id.strip()
    if role_key in ROLE_CODE_TO_NAME:
        role_name = ROLE_CODE_TO_NAME[role_key]
        role = await _get_role_by_name(session, role_name)
        if role is not None:
            return role

        role = await session.get(Role, role_uuid_from_code(role_key))
        if role is not None:
            return role

        role = Role(
            id=role_uuid_from_code(role_key),
            role_name=role_name,
            description=f"{role_name.title()} role",
        )
        session.add(role)
        await session.flush()
        return role

    try:
        role_uuid = UUID(role_key)
    except ValueError:
        valid_roles = ", ".join(f"{code}={name}" for code, name in ROLE_CODE_TO_NAME.items())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role_id. Use one of: {valid_roles}",
        )

    role = await session.get(Role, role_uuid)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with id {public_role_id} does not exist.",
        )
    return role


async def _get_role_by_name(session: AsyncSession, role_name: str) -> Role | None:
    result = await session.execute(select(Role).where(Role.role_name == role_name))
    return result.scalar_one_or_none()
