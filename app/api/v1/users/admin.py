from uuid import UUID

from fastapi import Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.api.v1.router_factory import build_crud_router
from app.core.database import get_db
from app.models.user import User
from app.schemas.admin_schema import AdminCreate, AdminResponse, AdminUpdate
from app.services.admin_service import admin_service

router = build_crud_router(admin_service, AdminCreate, AdminUpdate, AdminResponse)


def _ensure_admin(current_user: User) -> None:
    if current_user.role.role_name != "ADMIN":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can perform this action",
        )


@router.post("", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
async def create_admin(
    payload: AdminCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    return await admin_service.create(session, payload.model_dump())


@router.put("/{item_id}", response_model=AdminResponse)
async def update_admin(
    item_id: UUID,
    payload: AdminUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    return await admin_service.update(session, item_id, payload.model_dump(exclude_unset=True))


@router.delete("/{item_id}")
async def delete_admin(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    await admin_service.delete(session, item_id)
    return {"message": "Deleted successfully"}
