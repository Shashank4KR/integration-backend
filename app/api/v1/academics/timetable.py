from uuid import UUID

from fastapi import Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.api.v1.router_factory import build_crud_router
from app.core.database import get_db
from app.models.timetable_model import Timetable
from app.models.user import User
from app.schemas.timetable_schema import (
    TimetableCreate,
    TimetableResponse,
    TimetableUpdate,
)
from app.services.timetable_service import timetable_service

router = build_crud_router(
    timetable_service, TimetableCreate, TimetableUpdate, TimetableResponse
)


def _ensure_admin_or_teacher(current_user: User) -> None:
    if current_user.role.role_name not in ("ADMIN", "TEACHER"):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or teacher users can perform this action",
        )


@router.post("", response_model=TimetableResponse, status_code=status.HTTP_201_CREATED)
async def create_timetable(
    payload: TimetableCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_teacher(current_user)
    return await timetable_service.create(session, payload.model_dump())


@router.put("/{item_id}", response_model=TimetableResponse)
async def update_timetable(
    item_id: UUID,
    payload: TimetableUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_teacher(current_user)
    return await timetable_service.update(session, item_id, payload.model_dump(exclude_unset=True))


@router.delete("/{item_id}")
async def delete_timetable(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_teacher(current_user)
    await timetable_service.delete(session, item_id)
    return {"message": "Deleted successfully"}


@router.get("/teacher/{teacher_id}", response_model=list[TimetableResponse])
async def get_teacher_timetable(
    teacher_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    result = await session.execute(
        select(Timetable).where(Timetable.teacher_id == teacher_id)
    )
    return result.scalars().all()
