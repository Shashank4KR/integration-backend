from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.models.exam_result_model import ExamResult
from app.models.student_model import Student
from app.models.user import User
from app.schemas.exam_schema import (
    ExamResultCreate,
    ExamResultResponse,
    ExamResultUpdate,
)
from app.schemas.student_schema import StudentResponse
from app.services.exam_result_service import exam_result_service

router = APIRouter()


def _ensure_admin_or_teacher(current_user: User) -> None:
    if current_user.role.role_name not in ("ADMIN", "TEACHER"):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or teacher users can perform this action",
        )


@router.post("", response_model=ExamResultResponse, status_code=status.HTTP_201_CREATED)
async def create_exam_result(
    payload: ExamResultCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_teacher(current_user)
    return await exam_result_service.create(session, payload.model_dump())


@router.get("", response_model=list[ExamResultResponse])
async def list_exam_results(session: AsyncSession = Depends(get_db)):
    return await exam_result_service.list(session)


@router.get("/{item_id}", response_model=ExamResultResponse)
async def get_exam_result(item_id: UUID, session: AsyncSession = Depends(get_db)):
    return await exam_result_service.get(session, item_id)


@router.put("/{item_id}", response_model=ExamResultResponse)
async def update_exam_result(
    item_id: UUID,
    payload: ExamResultUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_teacher(current_user)
    return await exam_result_service.update(session, item_id, payload.model_dump(exclude_unset=True))


@router.delete("/{item_id}", status_code=status.HTTP_200_OK)
async def delete_exam_result(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_teacher(current_user)
    await exam_result_service.delete(session, item_id)
    return {"message": "Deleted successfully"}


@router.get("/teacher/{teacher_id}/students", response_model=list[StudentResponse])
async def get_teacher_students(
    teacher_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    from app.models.teacher_subject_model import TeacherSubject
    result = await session.execute(
        select(Student)
        .join(TeacherSubject, TeacherSubject.class_id == Student.class_id)
        .where(TeacherSubject.teacher_id == teacher_id)
        .distinct()
    )
    return result.scalars().all()
