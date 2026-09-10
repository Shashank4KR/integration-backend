from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.exam_models import ExamSubject, ExamInvigilator, ExamTimetable
from app.schemas.exam_schema import (
    ExamSubjectCreate,
    ExamSubjectResponse,
    ExamInvigilatorCreate,
    ExamInvigilatorResponse,
    ExamTimetableCreate,
    ExamTimetableResponse,
)

router = APIRouter()


def _ensure_admin(current_user: User) -> None:
    if current_user.role.role_name not in ("ADMIN", "TEACHER"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or teacher users can perform this action",
        )


# --- Exam Subjects ---

@router.get("/{exam_id}/subjects", response_model=list[ExamSubjectResponse])
async def list_exam_subjects(
    exam_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    result = await session.execute(
        select(ExamSubject).where(ExamSubject.exam_id == exam_id)
    )
    return result.scalars().all()


from pydantic import BaseModel

class ExamSubjectBatch(BaseModel):
    subject_ids: list[UUID]

@router.post("/{exam_id}/subjects", response_model=ExamSubjectResponse, status_code=status.HTTP_201_CREATED)
async def assign_exam_subject(
    exam_id: UUID,
    payload: ExamSubjectCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    # Check if already assigned
    existing = await session.execute(
        select(ExamSubject).where(
            ExamSubject.exam_id == exam_id,
            ExamSubject.subject_id == payload.subject_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subject already assigned to this exam"
        )
    
    exam_sub = ExamSubject(exam_id=exam_id, subject_id=payload.subject_id)
    session.add(exam_sub)
    await session.commit()
    await session.refresh(exam_sub)
    return exam_sub


@router.post("/{exam_id}/subjects/batch", status_code=status.HTTP_200_OK)
async def batch_assign_exam_subjects(
    exam_id: UUID,
    payload: ExamSubjectBatch,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    await session.execute(
        delete(ExamSubject).where(ExamSubject.exam_id == exam_id)
    )
    for sub_id in payload.subject_ids:
        exam_sub = ExamSubject(exam_id=exam_id, subject_id=sub_id)
        session.add(exam_sub)
    await session.commit()
    return {"message": "Subjects assigned successfully"}


# --- Exam Invigilators ---

@router.get("/{exam_id}/invigilators", response_model=list[ExamInvigilatorResponse])
async def list_exam_invigilators(
    exam_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    result = await session.execute(
        select(ExamInvigilator).where(ExamInvigilator.exam_id == exam_id)
    )
    return result.scalars().all()


@router.post("/{exam_id}/invigilators", response_model=ExamInvigilatorResponse, status_code=status.HTTP_201_CREATED)
async def assign_exam_invigilator(
    exam_id: UUID,
    payload: ExamInvigilatorCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    # Check if already assigned
    existing = await session.execute(
        select(ExamInvigilator).where(
            ExamInvigilator.exam_id == exam_id,
            ExamInvigilator.teacher_id == payload.teacher_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invigilator already assigned to this exam"
        )
    
    invigilator = ExamInvigilator(
        exam_id=exam_id,
        teacher_id=payload.teacher_id,
        room_no=payload.room_no,
        invigilator_date=payload.invigilator_date
    )
    session.add(invigilator)
    await session.commit()
    await session.refresh(invigilator)
    return invigilator


@router.delete("/{exam_id}/invigilators/{invigilator_id}", status_code=status.HTTP_200_OK)
async def remove_exam_invigilator(
    exam_id: UUID,
    invigilator_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    await session.execute(
        delete(ExamInvigilator).where(
            ExamInvigilator.id == invigilator_id,
            ExamInvigilator.exam_id == exam_id
        )
    )
    await session.commit()
    return {"message": "Deleted successfully"}


# --- Exam Timetable ---

@router.get("/{exam_id}/timetable", response_model=list[ExamTimetableResponse])
async def list_exam_timetable(
    exam_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    result = await session.execute(
        select(ExamTimetable).where(ExamTimetable.exam_id == exam_id)
    )
    return result.scalars().all()


@router.post("/{exam_id}/timetable", response_model=ExamTimetableResponse, status_code=status.HTTP_201_CREATED)
async def create_exam_timetable_entry(
    exam_id: UUID,
    payload: ExamTimetableCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    # Check if subject timetable already exists for this exam
    existing = await session.execute(
        select(ExamTimetable).where(
            ExamTimetable.exam_id == exam_id,
            ExamTimetable.subject_id == payload.subject_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Timetable entry for this subject already exists in this exam"
        )
    
    timetable = ExamTimetable(
        exam_id=exam_id,
        subject_id=payload.subject_id,
        exam_date=payload.exam_date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        room_no=payload.room_no
    )
    session.add(timetable)
    await session.commit()
    await session.refresh(timetable)
    return timetable


@router.delete("/{exam_id}/timetable/{timetable_id}", status_code=status.HTTP_200_OK)
async def delete_exam_timetable_entry(
    exam_id: UUID,
    timetable_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    await session.execute(
        delete(ExamTimetable).where(
            ExamTimetable.id == timetable_id,
            ExamTimetable.exam_id == exam_id
        )
    )
    await session.commit()
    return {"message": "Deleted successfully"}
