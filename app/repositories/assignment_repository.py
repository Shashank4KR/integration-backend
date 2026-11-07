from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment_model import Assignment, AssignmentSubmission
from app.repositories.crud_repository import CRUDRepository


class AssignmentRepository(CRUDRepository[Assignment]):
    async def get_by_id(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)
    async def get_all(self, session: AsyncSession):
        return await self.list(session)
    async def get_by_teacher(self, session: AsyncSession, teacher_id: UUID):
        return list((await session.execute(select(Assignment).where(Assignment.teacher_id == teacher_id))).scalars().all())
    async def get_by_class(self, session: AsyncSession, class_id: UUID):
        return list((await session.execute(select(Assignment).where(Assignment.class_id == class_id))).scalars().all())
    async def get_by_subject(self, session: AsyncSession, subject_id: UUID):
        return list((await session.execute(select(Assignment).where(Assignment.subject_id == subject_id))).scalars().all())


class AssignmentSubmissionRepository(CRUDRepository[AssignmentSubmission]):
    async def get_by_id(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)
    async def get_all(self, session: AsyncSession):
        return await self.list(session)
    async def get_by_student(self, session: AsyncSession, student_id: UUID):
        return list((await session.execute(select(AssignmentSubmission).where(AssignmentSubmission.student_id == student_id))).scalars().all())
    async def get_by_assignment(self, session: AsyncSession, assignment_id: UUID):
        return list((await session.execute(select(AssignmentSubmission).where(AssignmentSubmission.assignment_id == assignment_id))).scalars().all())


assignment_repository = AssignmentRepository(Assignment)
assignment_submission_repository = AssignmentSubmissionRepository(AssignmentSubmission)
