from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.core.security import hash_password
from app.models.user import User
from app.services.role_resolver import resolve_role
from app.schemas.user import (
    UserCreate,
    UserCreateResponse,
    UserUpdate,
    UserResponse,
)

router = APIRouter()


def _ensure_admin(current_user: User) -> None:
    if current_user.role.role_name != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can perform this action",
        )


@router.post(
    "/users",
    response_model=UserCreateResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_user(
    user_data: UserCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: User = Depends(get_current_user),
) -> UserCreateResponse:
    _ensure_admin(current_user)

    result = await session.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A user with email {user_data.email} already exists."
        )

    result = await session.execute(
        select(User).where(User.username == user_data.username)
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A user with username {user_data.username} already exists."
        )

    role = await resolve_role(session, user_data.role_id)

    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        phone=user_data.phone,
        status=user_data.status,
        role_id=role.id,
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    response = UserCreateResponse.model_validate(user)
    response.created_id = user.id
    return response


@router.get(
    "/users",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK
)
async def get_users(
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: User = Depends(get_current_user),
) -> list[UserResponse]:
    _ensure_admin(current_user)

    result = await session.execute(select(User))
    users = result.scalars().all()

    return [UserResponse.model_validate(user) for user in users]


@router.get(
    "/users/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.get(
    "/users/{id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK
)
async def get_user(
    id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    _ensure_admin(current_user)

    result = await session.execute(select(User).where(User.id == id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse.model_validate(user)


@router.put(
    "/users/{id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK
)
async def update_user(
    id: UUID,
    user_data: UserUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    _ensure_admin(current_user)

    result = await session.execute(select(User).where(User.id == id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    update_data = user_data.model_dump(exclude_unset=True)

    if "email" in update_data:
        result = await session.execute(
            select(User).where(User.email == update_data["email"], User.id != id)
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists",
            )

    if "username" in update_data:
        result = await session.execute(
            select(User).where(User.username == update_data["username"], User.id != id)
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists",
            )

    if "password" in update_data:
        plain_password = update_data.pop("password")
        update_data["password_hash"] = hash_password(plain_password)

    if "role_id" in update_data:
        role = await resolve_role(session, update_data["role_id"])
        update_data["role_id"] = role.id

    for field, value in update_data.items():
        setattr(user, field, value)

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return UserResponse.model_validate(user)


@router.delete(
    "/users/{id}",
    status_code=status.HTTP_200_OK
)
async def delete_user(
    id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: User = Depends(get_current_user),
) -> dict:
    _ensure_admin(current_user)

    result = await session.execute(select(User).where(User.id == id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    await session.delete(user)
    await session.commit()

    return {"message": "User deleted successfully"}
