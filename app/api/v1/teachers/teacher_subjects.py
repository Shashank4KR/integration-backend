from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.teacher_subject_schema import (
    TeacherSubjectCreate,
    TeacherSubjectResponse,
)
from app.services.teacher_subject_service import teacher_subject_service

router = APIRouter()


def _ensure_admin_or_teacher(current_user: User) -> None:
    role_name = (current_user.role.role_name if current_user.role else "").upper()
    if role_name not in ("ADMIN", "TEACHER"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or teacher users can perform this action",
        )


@router.post("", response_model=TeacherSubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_teacher_subject(
    payload: TeacherSubjectCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_teacher(current_user)
    return await teacher_subject_service.create(session, payload.model_dump())


@router.get("", response_model=list[TeacherSubjectResponse])
async def list_teacher_subjects(session: AsyncSession = Depends(get_db)):
    return await teacher_subject_service.list(session)


@router.get("/{item_id}", response_model=TeacherSubjectResponse)
async def get_teacher_subject(item_id: UUID, session: AsyncSession = Depends(get_db)):
    return await teacher_subject_service.get(session, item_id)


@router.delete("/{item_id}", status_code=status.HTTP_200_OK)
async def delete_teacher_subject(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_teacher(current_user)
    await teacher_subject_service.delete(session, item_id)
    return {"message": "Deleted successfully"}

