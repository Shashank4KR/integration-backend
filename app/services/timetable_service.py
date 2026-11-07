from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.timetable_model import Timetable
from app.repositories.timetable_repository import timetable_repository
from app.services.crud_service import TIMETABLE_FKS, CRUDService


class TimetableService(CRUDService):
    async def create(self, session: AsyncSession, data: dict[str, Any]) -> Any:
        await self._validate_time_range(data)
        await self._validate_foreign_keys(session, data)
        await self._validate_conflicts(session, data)
        item = await self.repository.create(session, data)
        await session.commit()
        return item

    async def update(
        self, session: AsyncSession, item_id: UUID, data: dict[str, Any]
    ) -> Any:
        item = await self.get(session, item_id)
        merged = {
            "class_id": item.class_id,
            "subject_id": item.subject_id,
            "teacher_id": item.teacher_id,
            "day_of_week": item.day_of_week,
            "start_time": item.start_time,
            "end_time": item.end_time,
            "room_no": item.room_no,
            "period_no": item.period_no,
        }
        merged.update(data)
        await self._validate_time_range(merged)
        await self._validate_foreign_keys(session, merged)
        await self._validate_conflicts(session, merged, exclude_id=item_id)
        item = await self.repository.update(session, item, data)
        await session.commit()
        return item

    async def _validate_time_range(self, data: dict[str, Any]) -> None:
        if data["end_time"] <= data["start_time"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="end_time must be after start_time",
            )

    async def _validate_conflicts(
        self,
        session: AsyncSession,
        data: dict[str, Any],
        exclude_id: UUID | None = None,
    ) -> None:
        overlap_filter = and_(
            Timetable.day_of_week == data["day_of_week"],
            Timetable.start_time < data["end_time"],
            Timetable.end_time > data["start_time"],
        )

        teacher_query = select(Timetable).where(
            overlap_filter,
            Timetable.teacher_id == data["teacher_id"],
        )
        class_query = select(Timetable).where(
            overlap_filter,
            Timetable.class_id == data["class_id"],
        )
        if exclude_id is not None:
            teacher_query = teacher_query.where(Timetable.id != exclude_id)
            class_query = class_query.where(Timetable.id != exclude_id)

        teacher_conflict = (await session.execute(teacher_query)).scalar_one_or_none()
        if teacher_conflict is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Teacher already has a timetable entry during this time",
            )

        class_conflict = (await session.execute(class_query)).scalar_one_or_none()
        if class_conflict is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Class already has a timetable entry during this time",
            )


timetable_service = TimetableService(
    timetable_repository, "Timetable", foreign_keys=TIMETABLE_FKS
)
