from typing import Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.class_repository import class_repository
from app.services.crud_service import CLASS_FKS, CRUDService
from app.models.class_subject_model import ClassSubject
from app.models.teacher_subject_model import TeacherSubject
from app.models.timetable_model import Timetable
from app.models.exam_result_model import ExamResult
from app.models.exam_model import Exam
from app.models.subject_model import Subject
from app.models.teacher_model import Teacher

class ClassService(CRUDService):
    async def get_class_subjects(self, session: AsyncSession, class_id: UUID) -> list[Subject]:
        result = await session.execute(
            select(Subject)
            .join(ClassSubject, ClassSubject.subject_id == Subject.id)
            .where(ClassSubject.class_id == class_id)
        )
        return list(result.scalars().all())

    async def get_class_teachers(self, session: AsyncSession, class_id: UUID) -> list[Teacher]:
        result = await session.execute(
            select(Teacher)
            .join(TeacherSubject, TeacherSubject.teacher_id == Teacher.id)
            .where(TeacherSubject.class_id == class_id)
            .distinct()
        )
        return list(result.scalars().all())

    async def get_class_timetable(self, session: AsyncSession, class_id: UUID) -> list[Timetable]:
        result = await session.execute(
            select(Timetable)
            .where(Timetable.class_id == class_id)
        )
        return list(result.scalars().all())

    async def get_class_exams(self, session: AsyncSession, class_id: UUID) -> list[ExamResult]:
        result = await session.execute(
            select(ExamResult)
            .join(Exam, Exam.id == ExamResult.exam_id)
            .where(Exam.class_id == class_id)
        )
        return list(result.scalars().all())

class_service = ClassService(
    class_repository,
    "Class",
    unique_constraints=(("class_name", "section", "academic_year"),),
    foreign_keys=CLASS_FKS,
)
