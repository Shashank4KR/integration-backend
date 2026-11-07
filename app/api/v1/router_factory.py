from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import create_model
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.models.user import User


def _role_name(user: User) -> str:
    return (user.role.role_name if user.role else "").upper()


def require_roles(user: User, allowed_roles: tuple[str, ...]) -> None:
    normalized_allowed = {role.upper() for role in allowed_roles}
    if _role_name(user) not in normalized_allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource",
        )


def build_crud_router(
    service: Any,
    create_schema: type,
    update_schema: type,
    response_schema: type,
    read_roles: tuple[str, ...] = ("ADMIN",),
    write_roles: tuple[str, ...] = ("ADMIN",),
    get_checker: Any | None = None,
) -> APIRouter:
    router = APIRouter()

    PaginatedResponse = create_model(
        f"Paginated{response_schema.__name__}",
        items=(list[response_schema], ...),
        total=(int, ...),
    )

    @router.post("", response_model=response_schema, status_code=status.HTTP_201_CREATED)
    async def create(
        payload: create_schema,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        require_roles(current_user, write_roles)
        return await service.create(session, payload.model_dump())

    @router.get("", response_model=PaginatedResponse)
    async def list_items(
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        require_roles(current_user, read_roles)
        return await service.list(session, limit=limit, offset=offset)

    @router.get("/{item_id:uuid}", response_model=response_schema)
    async def get(
        item_id: UUID,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        if get_checker is not None:
            await get_checker(session, current_user, item_id)
        else:
            require_roles(current_user, read_roles)
        return await service.get(session, item_id)

    @router.put("/{item_id:uuid}", response_model=response_schema)
    async def update(
        item_id: UUID,
        payload: update_schema,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        require_roles(current_user, write_roles)
        return await service.update(
            session, item_id, payload.model_dump(exclude_unset=True)
        )

    @router.delete("/{item_id:uuid}", status_code=status.HTTP_200_OK)
    async def delete(
        item_id: UUID,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        require_roles(current_user, write_roles)
        await service.delete(session, item_id)
        return {"message": "Deleted successfully"}

    return router
