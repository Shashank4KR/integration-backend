from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance_model import Attendance


class AttendanceRepository:
    async def create(
        self, session: AsyncSession, data: dict
    ) -> Attendance:
        attendance = Attendance(**data)
        session.add(attendance)
        await session.flush()
        await session.refresh(attendance)
        return attendance

    async def get_by_id(
        self, session: AsyncSession, attendance_id: UUID
    ) -> Attendance | None:
        return await session.get(Attendance, attendance_id)

    async def get_all(
        self,
        session: AsyncSession,
        class_id: UUID | None = None,
        student_id: UUID | None = None,
        teacher_id: UUID | None = None,
        subject_id: UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        status: str | None = None,
    ) -> list[Attendance]:
        stmt = select(Attendance)
        if class_id:
            stmt = stmt.where(Attendance.class_id == class_id)
        if student_id:
            stmt = stmt.where(Attendance.student_id == student_id)
        if teacher_id:
            stmt = stmt.where(Attendance.teacher_id == teacher_id)
        if subject_id:
            stmt = stmt.where(Attendance.subject_id == subject_id)
        if start_date:
            stmt = stmt.where(Attendance.attendance_date >= start_date)
        if end_date:
            stmt = stmt.where(Attendance.attendance_date <= end_date)
        if status:
            stmt = stmt.where(Attendance.status == status)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self, session: AsyncSession, attendance: Attendance, data: dict
    ) -> Attendance:
        for field, value in data.items():
            setattr(attendance, field, value)
        session.add(attendance)
        await session.flush()
        await session.refresh(attendance)
        return attendance

    async def delete(self, session: AsyncSession, attendance: Attendance) -> None:
        await session.delete(attendance)
        await session.flush()

    async def get_by_student(
        self, session: AsyncSession, student_id: UUID
    ) -> list[Attendance]:
        result = await session.execute(
            select(Attendance).where(Attendance.student_id == student_id)
        )
        return list(result.scalars().all())

    async def get_by_teacher(
        self, session: AsyncSession, teacher_id: UUID
    ) -> list[Attendance]:
        result = await session.execute(
            select(Attendance).where(Attendance.teacher_id == teacher_id)
        )
        return list(result.scalars().all())

    async def get_by_class(
        self, session: AsyncSession, class_id: UUID
    ) -> list[Attendance]:
        result = await session.execute(
            select(Attendance).where(Attendance.class_id == class_id)
        )
        return list(result.scalars().all())

    async def get_by_subject(
        self, session: AsyncSession, subject_id: UUID
    ) -> list[Attendance]:
        result = await session.execute(
            select(Attendance).where(Attendance.subject_id == subject_id)
        )
        return list(result.scalars().all())

    async def get_by_date(
        self, session: AsyncSession, attendance_date: date
    ) -> list[Attendance]:
        result = await session.execute(
            select(Attendance).where(Attendance.attendance_date == attendance_date)
        )
        return list(result.scalars().all())

    async def get_student_report(
        self,
        session: AsyncSession,
        student_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[Attendance]:
        result = await session.execute(
            select(Attendance).where(
                Attendance.student_id == student_id,
                Attendance.attendance_date >= start_date,
                Attendance.attendance_date <= end_date,
            )
        )
        return list(result.scalars().all())

    async def get_duplicate(
        self,
        session: AsyncSession,
        student_id: UUID,
        attendance_date: date,
        period_no: int,
        subject_id: UUID,
    ) -> Attendance | None:
        result = await session.execute(
            select(Attendance).where(
                Attendance.student_id == student_id,
                Attendance.attendance_date == attendance_date,
                Attendance.period_no == period_no,
                Attendance.subject_id == subject_id,
            )
        )
        return result.scalar_one_or_none()


attendance_repository = AttendanceRepository()
