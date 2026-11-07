from calendar import monthrange
from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event_model import AcademicCalendarEventType, EventType
from app.models.user import User
from app.repositories.event_repository import academic_calendar_repository, event_repository
from app.services.crud_service import CRUDService

EVENT_TYPES = {event_type.value for event_type in EventType}
ACADEMIC_CALENDAR_EVENT_TYPES = {event_type.value for event_type in AcademicCalendarEventType}


def _bad_request(detail: str) -> None:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class EventService(CRUDService):
    async def create_event(self, session: AsyncSession, data: dict):
        self._validate_event_data(data)
        if await session.get(User, data["created_by"]) is None:
            _bad_request("Creator user must exist")
        return await self.create(session, data)

    async def update_event(self, session: AsyncSession, item_id: UUID, data: dict):
        item = await self.get(session, item_id)
        self._validate_event_data(data, item)
        return await self.update(session, item_id, data)

    async def delete_event(self, session: AsyncSession, item_id: UUID): return await self.delete(session, item_id)
    async def get_event(self, session: AsyncSession, item_id: UUID): return await self.get(session, item_id)
    async def get_events(self, session: AsyncSession):
        res = await self.list(session)
        return res["items"] if isinstance(res, dict) and "items" in res else res

    def _validate_event_data(self, data: dict, existing=None) -> None:
        if "event_name" in data and not data["event_name"].strip(): _bad_request("Event name cannot be empty")
        if "event_type" in data and data["event_type"] not in EVENT_TYPES: _bad_request("Invalid event type")
        start_date = data.get("start_date", getattr(existing, "start_date", None))
        end_date = data.get("end_date", getattr(existing, "end_date", None))
        if start_date and end_date and start_date > end_date: _bad_request("Start date cannot be after end date")

    async def get_by_type(self, session: AsyncSession, event_type: str):
        if event_type not in EVENT_TYPES: _bad_request("Invalid event type")
        return await self.repository.get_by_type(session, event_type)

    async def get_by_date_range(self, session: AsyncSession, start_date: date, end_date: date):
        if start_date > end_date: _bad_request("Start date cannot be after end date")
        return await self.repository.get_by_date_range(session, start_date, end_date)

    async def get_upcoming(self, session: AsyncSession): return await self.repository.get_upcoming(session, date.today())

    async def get_summary(self, session: AsyncSession) -> dict:
        events_res = await self.list(session)
        events = events_res["items"] if isinstance(events_res, dict) and "items" in events_res else events
        holidays = await academic_calendar_repository.get_holidays(session)
        return {"total_events": len(events), "upcoming_events": sum(e.start_date >= date.today() for e in events), "holidays": len(holidays), "academic_events": sum(e.event_type == "ACADEMIC" for e in events)}


class AcademicCalendarService(CRUDService):
    async def create_calendar_entry(self, session: AsyncSession, data: dict):
        self._validate_calendar_data(data)
        return await self.create(session, data)

    async def update_calendar_entry(self, session: AsyncSession, item_id: UUID, data: dict):
        item = await self.get(session, item_id)
        self._validate_calendar_data(data, item)
        return await self.update(session, item_id, data)

    async def delete_calendar_entry(self, session: AsyncSession, item_id: UUID): return await self.delete(session, item_id)
    async def get_calendar_entry(self, session: AsyncSession, item_id: UUID): return await self.get(session, item_id)
    async def get_calendar_entries(self, session: AsyncSession):
        res = await self.list(session)
        return res["items"] if isinstance(res, dict) and "items" in res else res

    def _validate_calendar_data(self, data: dict, existing=None) -> None:
        if "title" in data and not data["title"].strip(): _bad_request("Title cannot be empty")
        if "event_type" in data and data["event_type"] not in ACADEMIC_CALENDAR_EVENT_TYPES: _bad_request("Invalid academic calendar event type")
        start_date = data.get("start_date", getattr(existing, "start_date", None))
        end_date = data.get("end_date", getattr(existing, "end_date", None))
        if start_date and end_date and start_date > end_date: _bad_request("Start date cannot be after end date")

    async def get_by_month(self, session: AsyncSession, year: int, month: int):
        if not 1 <= month <= 12: _bad_request("Month must be between 1 and 12")
        start_date, end_date = date(year, month, 1), date(year, month, monthrange(year, month)[1])
        return await self.repository.get_by_month(session, start_date, end_date)

    async def get_holidays(self, session: AsyncSession): return await self.repository.get_holidays(session)


event_service = EventService(event_repository, "Event")
academic_calendar_service = AcademicCalendarService(academic_calendar_repository, "Academic calendar entry")
