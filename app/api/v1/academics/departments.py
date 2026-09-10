from uuid import UUID

from fastapi import Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.api.v1.router_factory import build_crud_router
from app.core.database import get_db
from app.models.user import User
from app.schemas.department_schema import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
)
from app.services.department_service import department_service

router = build_crud_router(
    department_service, DepartmentCreate, DepartmentUpdate, DepartmentResponse
)


def _ensure_admin(current_user: User) -> None:
    if current_user.role.role_name != "ADMIN":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can perform this action",
        )


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    payload: DepartmentCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    return await department_service.create(session, payload.model_dump())


@router.put("/{item_id}", response_model=DepartmentResponse)
async def update_department(
    item_id: UUID,
    payload: DepartmentUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    return await department_service.update(session, item_id, payload.model_dump(exclude_unset=True))


@router.delete("/{item_id}")
async def delete_department(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    await department_service.delete(session, item_id)
    return {"message": "Deleted successfully"}
