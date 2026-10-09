from collections import Counter
from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance_model import AttendanceStatus
from app.models.class_model import Class
from app.models.class_subject_model import ClassSubject
from app.models.student_model import Student
from app.models.subject_model import Subject
from app.models.teacher_model import Teacher
from app.models.teacher_subject_model import TeacherSubject
from app.models.user import User
from app.repositories.attendance_repository import attendance_repository


class AttendanceService:
    async def create_attendance(self, session: AsyncSession, data: dict):
        await self._validate_payload(session, data)
        attendance = await attendance_repository.create(session, data)
        await session.commit()
        return attendance

    async def update_attendance(
        self, session: AsyncSession, attendance_id: UUID, data: dict
    ):
        attendance = await self.get_attendance(session, attendance_id)
        status_value = self._validate_status(data["status"])
        attendance = await attendance_repository.update(
            session, attendance, {"status": status_value}
        )
        await session.commit()
        return attendance

    async def delete_attendance(self, session: AsyncSession, attendance_id: UUID) -> None:
        attendance = await self.get_attendance(session, attendance_id)
        await attendance_repository.delete(session, attendance)
        await session.commit()

    async def get_attendance(self, session: AsyncSession, attendance_id: UUID):
        attendance = await attendance_repository.get_by_id(session, attendance_id)
        if attendance is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Attendance not found"
            )
        return attendance

    async def get_all_attendance(
        self,
        session: AsyncSession,
        class_id: UUID | None = None,
        student_id: UUID | None = None,
        teacher_id: UUID | None = None,
        subject_id: UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        status: str | None = None,
        academic_year: str | None = None,
    ):
        return await attendance_repository.get_all(
            session,
            class_id=class_id,
            student_id=student_id,
            teacher_id=teacher_id,
            subject_id=subject_id,
            start_date=start_date,
            end_date=end_date,
            status=status,
            academic_year=academic_year,
        )

    async def get_student_attendance(self, session: AsyncSession, student_id: UUID):
        await self._require_exists(session, Student, student_id, "Student")
        return await attendance_repository.get_by_student(session, student_id)

    async def get_class_attendance(self, session: AsyncSession, class_id: UUID):
        await self._require_exists(session, Class, class_id, "Class")
        return await attendance_repository.get_by_class(session, class_id)

    async def get_teacher_attendance(self, session: AsyncSession, teacher_id: UUID):
        await self._require_exists(session, Teacher, teacher_id, "Teacher")
        return await attendance_repository.get_by_teacher(session, teacher_id)

    async def get_date_attendance(self, session: AsyncSession, attendance_date: date):
        return await attendance_repository.get_by_date(session, attendance_date)

    async def get_student_report(
        self, session: AsyncSession, student_id: UUID, start_date: date, end_date: date
    ):
        await self._require_exists(session, Student, student_id, "Student")
        return await attendance_repository.get_student_report(
            session, student_id, start_date, end_date
        )

    async def get_student_summary(self, session: AsyncSession, student_id: UUID) -> dict:
        records = await self.get_student_attendance(session, student_id)
        counts = self._count_statuses(records)
        total = len(records)
        percentage = round(((counts["PRESENT"] + counts["LATE"]) / total) * 100, 2) if total else 0
        return {
            "student_id": student_id,
            "total_classes": total,
            "present": counts["PRESENT"],
            "absent": counts["ABSENT"],
            "late": counts["LATE"],
            "attendance_percentage": percentage,
        }

    async def create_bulk_attendance(self, session: AsyncSession, data: dict):
        if not data["records"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="records cannot be empty",
            )
        await self._validate_assignment(session, data)
        await self._require_exists(session, User, data["marked_by"], "Marked by user")

        created = []
        try:
            for record in data["records"]:
                payload = {
                    "student_id": record["student_id"],
                    "class_id": data["class_id"],
                    "subject_id": data["subject_id"],
                    "teacher_id": data["teacher_id"],
                    "attendance_date": data["attendance_date"],
                    "period_no": data["period_no"],
                    "status": record["status"],
                    "marked_by": data["marked_by"],
                }
                await self._validate_student(session, payload["student_id"], data["class_id"])
                await self._validate_duplicate(session, payload)
                payload["status"] = self._validate_status(payload["status"])
                created.append(await attendance_repository.create(session, payload))
            await session.commit()
            return created
        except Exception:
            await session.rollback()
            raise

    async def get_class_summary(self, session: AsyncSession, class_id: UUID) -> dict:
        await self._require_exists(session, Class, class_id, "Class")
        records = await attendance_repository.get_by_class(session, class_id)
        counts = self._count_statuses(records)
        total_students = (
            await session.execute(
                select(func.count(Student.id)).where(Student.class_id == class_id)
            )
        ).scalar_one()
        return {
            "class_id": class_id,
            "total_students": total_students,
            "present": counts["PRESENT"],
            "absent": counts["ABSENT"],
            "late": counts["LATE"],
        }

    async def get_subject_summary(self, session: AsyncSession, subject_id: UUID) -> dict:
        await self._require_exists(session, Subject, subject_id, "Subject")
        records = await attendance_repository.get_by_subject(session, subject_id)
        counts = self._count_statuses(records)
        return {
            "subject_id": subject_id,
            "total_records": len(records),
            "present": counts["PRESENT"],
            "absent": counts["ABSENT"],
            "late": counts["LATE"],
        }

    async def get_teacher_summary(self, session: AsyncSession, teacher_id: UUID) -> dict:
        await self._require_exists(session, Teacher, teacher_id, "Teacher")
        records = await attendance_repository.get_by_teacher(session, teacher_id)
        counts = self._count_statuses(records)
        return {
            "teacher_id": teacher_id,
            "total_records": len(records),
            "present": counts["PRESENT"],
            "absent": counts["ABSENT"],
            "late": counts["LATE"],
        }

    async def _validate_payload(self, session: AsyncSession, data: dict) -> None:
        data["status"] = self._validate_status(data["status"])
        await self._validate_assignment(session, data)
        await self._validate_student(session, data["student_id"], data["class_id"])
        await self._require_exists(session, User, data["marked_by"], "Marked by user")
        await self._validate_duplicate(session, data)

    def _validate_status(self, status_value: str) -> str:
        normalized = status_value.upper()
        if normalized not in AttendanceStatus.__members__:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="status must be one of PRESENT, ABSENT, LATE",
            )
        return normalized

    async def _validate_assignment(self, session: AsyncSession, data: dict) -> None:
        await self._require_exists(session, Class, data["class_id"], "Class")
        await self._require_exists(session, Subject, data["subject_id"], "Subject")
        await self._require_exists(session, Teacher, data["teacher_id"], "Teacher")

        teacher_subject = (
            await session.execute(
                select(TeacherSubject).where(
                    TeacherSubject.teacher_id == data["teacher_id"],
                    TeacherSubject.subject_id == data["subject_id"],
                    TeacherSubject.class_id == data["class_id"],
                )
            )
        ).scalar_one_or_none()
        if teacher_subject is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Teacher is not assigned to this subject for this class",
            )

        class_subject = (
            await session.execute(
                select(ClassSubject).where(
                    ClassSubject.class_id == data["class_id"],
                    ClassSubject.subject_id == data["subject_id"],
                )
            )
        ).scalar_one_or_none()
        if class_subject is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subject does not belong to this class",
            )

    async def _validate_student(
        self, session: AsyncSession, student_id: UUID, class_id: UUID
    ) -> None:
        student = await self._require_exists(session, Student, student_id, "Student")
        if student.class_id != class_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student does not belong to this class",
            )

    async def _validate_duplicate(self, session: AsyncSession, data: dict) -> None:
        duplicate = await attendance_repository.get_duplicate(
            session,
            data["student_id"],
            data["attendance_date"],
            data["period_no"],
            data["subject_id"],
        )
        if duplicate is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Attendance already marked for this student, subject, date and period",
            )

    async def _require_exists(
        self, session: AsyncSession, model: type, item_id: UUID, entity_name: str
    ):
        item = await session.get(model, item_id)
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{entity_name} not found",
            )
        return item

    def _count_statuses(self, records) -> Counter:
        return Counter(record.status.value if hasattr(record.status, "value") else record.status for record in records)


attendance_service = AttendanceService()
