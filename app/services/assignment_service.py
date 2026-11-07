from datetime import UTC, datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment_model import Assignment, AssignmentSubmission
from app.models.student_model import Student
from app.models.teacher_subject_model import TeacherSubject
from app.repositories.assignment_repository import assignment_repository, assignment_submission_repository
from app.services.crud_service import CRUDService


class AssignmentService(CRUDService):
    async def create(self, session: AsyncSession, data: dict):
        await self._validate_assignment(session, data)
        return await super().create(session, data)
    async def update(self, session: AsyncSession, item_id: UUID, data: dict):
        item = await self.get(session, item_id)
        merged = {field: getattr(item, field) for field in ("teacher_id", "class_id", "subject_id", "due_date")}
        merged.update(data)
        await self._validate_assignment(session, merged)
        return await super().update(session, item_id, data)
    async def _validate_assignment(self, session, data):
        due_date = data["due_date"]
        if due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=UTC)
        if due_date <= datetime.now(UTC):
            raise HTTPException(status_code=400, detail="due_date must be in the future")
        assigned = (await session.execute(select(TeacherSubject).where(TeacherSubject.teacher_id == data["teacher_id"], TeacherSubject.class_id == data["class_id"], TeacherSubject.subject_id == data["subject_id"]))).scalar_one_or_none()
        if assigned is None:
            raise HTTPException(status_code=400, detail="Teacher is not assigned to this class and subject")
    async def create_assignment(self, session, data): return await self.create(session, data)
    async def update_assignment(self, session, item_id, data): return await self.update(session, item_id, data)
    async def delete_assignment(self, session, item_id): return await self.delete(session, item_id)
    async def get_assignment(self, session, item_id): return await self.get(session, item_id)
    async def get_assignments(self, session): return await self.list(session)
    async def summary(self, session, assignment_id: UUID):
        assignment = await self.get(session, assignment_id)
        total = (await session.execute(select(func.count()).select_from(Student).where(Student.class_id == assignment.class_id))).scalar_one()
        submitted = (await session.execute(select(func.count()).select_from(AssignmentSubmission).where(AssignmentSubmission.assignment_id == assignment_id))).scalar_one()
        return {"assignment_id": assignment_id, "total_students": total, "submitted": submitted, "pending": total - submitted}


class SubmissionService(CRUDService):
    async def create(self, session, data):
        await self._validate_submission(session, data)
        if await self.repository.get_by_fields(session, {"assignment_id": data["assignment_id"], "student_id": data["student_id"]}):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Student has already submitted this assignment")
        return await super().create(session, data)
    async def update(self, session, item_id, data):
        if data.get("marks") is not None and data["marks"] < 0: raise HTTPException(status_code=400, detail="marks cannot be negative")
        return await super().update(session, item_id, data)
    async def _validate_submission(self, session, data):
        assignment = await session.get(Assignment, data["assignment_id"])
        student = await session.get(Student, data["student_id"])
        if assignment is None or student is None: raise HTTPException(status_code=404, detail="Assignment or student not found")
        if student.class_id != assignment.class_id: raise HTTPException(status_code=400, detail="Student does not belong to assignment class")
        if data.get("marks") is not None and data["marks"] < 0: raise HTTPException(status_code=400, detail="marks cannot be negative")
    async def submit_assignment(self, session, data): return await self.create(session, data)
    async def update_submission(self, session, item_id, data): return await self.update(session, item_id, data)
    async def delete_submission(self, session, item_id): return await self.delete(session, item_id)
    async def get_submission(self, session, item_id): return await self.get(session, item_id)
    async def get_submissions(self, session): return await self.list(session)


assignment_service = AssignmentService(assignment_repository, "Assignment")
submission_service = SubmissionService(assignment_submission_repository, "Assignment submission")
