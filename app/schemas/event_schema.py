from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EventCreate(BaseModel):
    event_name: str
    event_type: str
    description: str | None = None
    start_date: date
    end_date: date
    venue: str | None = None
    created_by: UUID | None = None


class EventUpdate(BaseModel):
    event_name: str | None = None
    event_type: str | None = None
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    venue: str | None = None


class EventResponse(EventCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime


class AcademicCalendarCreate(BaseModel):
    title: str
    event_type: str
    start_date: date
    end_date: date
    description: str | None = None
    is_holiday: bool = False


class AcademicCalendarUpdate(BaseModel):
    title: str | None = None
    event_type: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = None
    is_holiday: bool | None = None


class AcademicCalendarResponse(AcademicCalendarCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime
