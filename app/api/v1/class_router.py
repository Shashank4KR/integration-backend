from uuid import UUID

from fastapi import Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.api.v1.router_factory import build_crud_router
from app.core.database import get_db
from app.models.class_subject_model import ClassSubject
from app.models.exam_model import Exam
from app.models.exam_result_model import ExamResult
from app.models.subject_model import Subject
from app.models.teacher_model import Teacher
from app.models.teacher_subject_model import TeacherSubject
from app.models.timetable_model import Timetable
from app.models.user import User
from app.schemas.class_schema import (
    ClassCreate,
    ClassResponse,
    ClassSubjectSummary,
    ClassTeacherSummary,
    ClassUpdate,
)
from app.schemas.exam_schema import ExamResultResponse
from app.schemas.timetable_schema import TimetableResponse
from app.services.class_service import class_service

router = build_crud_router(class_service, ClassCreate, ClassUpdate, ClassResponse)


def _ensure_admin_or_teacher(current_user: User) -> None:
    if current_user.role.role_name not in ("ADMIN", "TEACHER"):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or teacher users can perform this action",
        )


@router.post("", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
async def create_class(
    payload: ClassCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_teacher(current_user)
    return await class_service.create(session, payload.model_dump())


@router.put("/{item_id}", response_model=ClassResponse)
async def update_class(
    item_id: UUID,
    payload: ClassUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_teacher(current_user)
    return await class_service.update(session, item_id, payload.model_dump(exclude_unset=True))


@router.delete("/{item_id}")
async def delete_class(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_teacher(current_user)
    await class_service.delete(session, item_id)
    return {"message": "Deleted successfully"}


@router.get("/{class_id}/subjects", response_model=list[ClassSubjectSummary])
async def get_class_subjects(class_id: UUID, session: AsyncSession = Depends(get_db)):
    return await class_service.get_class_subjects(session, class_id)


@router.get("/{class_id}/teachers", response_model=list[ClassTeacherSummary])
async def get_class_teachers(class_id: UUID, session: AsyncSession = Depends(get_db)):
    return await class_service.get_class_teachers(session, class_id)


from app.schemas.student import StudentResponse
from app.models.student_model import Student

@router.get("/{class_id}/students", response_model=list[StudentResponse])
async def get_class_students(class_id: UUID, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Student).where(Student.class_id == class_id))
    return result.scalars().all()



@router.get("/{class_id}/timetable", response_model=list[TimetableResponse])
async def get_class_timetable(class_id: UUID, session: AsyncSession = Depends(get_db)):
    return await class_service.get_class_timetable(session, class_id)


@router.get("/{class_id}/exams", response_model=list[ExamResultResponse])
async def get_class_exams(class_id: UUID, session: AsyncSession = Depends(get_db)):
    return await class_service.get_class_exams(session, class_id)


@router.get("/{class_id}/subjects", response_model=list[ClassSubjectSummary])
async def get_subjects_for_class(
    class_id: UUID, session: AsyncSession = Depends(get_db)
):
    await class_service.get(session, class_id)
    result = await session.execute(
        select(Subject)
        .join(ClassSubject, ClassSubject.subject_id == Subject.id)
        .where(ClassSubject.class_id == class_id)
    )
    return result.scalars().all()


@router.get("/{class_id}/exam-results", response_model=list[ExamResultResponse])
async def get_class_exam_results(
    class_id: UUID, session: AsyncSession = Depends(get_db)
):
    await class_service.get(session, class_id)
    result = await session.execute(
        select(ExamResult)
        .join(Exam, ExamResult.exam_id == Exam.id)
        .where(Exam.class_id == class_id)
    )
    return result.scalars().all()


@router.get("/{class_id}/teachers", response_model=list[ClassTeacherSummary])
async def get_teachers_for_class(
    class_id: UUID, session: AsyncSession = Depends(get_db)
):
    await class_service.get(session, class_id)
    result = await session.execute(
        select(Teacher)
        .join(TeacherSubject, TeacherSubject.teacher_id == Teacher.id)
        .where(TeacherSubject.class_id == class_id)
        .distinct()
    )
    return result.scalars().all()


@router.get("/{class_id}/timetable", response_model=list[TimetableResponse])
async def get_timetable_for_class(
    class_id: UUID, session: AsyncSession = Depends(get_db)
):
    await class_service.get(session, class_id)
    result = await session.execute(
        select(Timetable).where(Timetable.class_id == class_id)
    )
    return result.scalars().all()
