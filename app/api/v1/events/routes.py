from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.event_schema import AcademicCalendarCreate, AcademicCalendarResponse, AcademicCalendarUpdate, EventCreate, EventResponse, EventUpdate
from app.services.event_service import academic_calendar_service, event_service

event_router = APIRouter()


def _ensure_admin(current_user: User) -> None:
    if current_user.role.role_name != "ADMIN":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can perform this action",
        )


@event_router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(payload: EventCreate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    return await event_service.create_event(session, payload.model_dump())

@event_router.get("", response_model=list[EventResponse])
async def get_events(session: AsyncSession = Depends(get_db)): return await event_service.get_events(session)

@event_router.get("/type/{event_type}", response_model=list[EventResponse])
async def get_events_by_type(event_type: str, session: AsyncSession = Depends(get_db)): return await event_service.get_by_type(session, event_type)

@event_router.get("/date-range", response_model=list[EventResponse])
async def get_events_by_date_range(start_date: date, end_date: date, session: AsyncSession = Depends(get_db)): return await event_service.get_by_date_range(session, start_date, end_date)

@event_router.get("/upcoming", response_model=list[EventResponse])
async def get_upcoming_events(session: AsyncSession = Depends(get_db)): return await event_service.get_upcoming(session)

@event_router.get("/summary")
async def get_events_summary(session: AsyncSession = Depends(get_db)): return await event_service.get_summary(session)

@event_router.get("/{item_id}", response_model=EventResponse)
async def get_event(item_id: UUID, session: AsyncSession = Depends(get_db)): return await event_service.get_event(session, item_id)

@event_router.put("/{item_id}", response_model=EventResponse)
async def update_event(item_id: UUID, payload: EventUpdate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    return await event_service.update_event(session, item_id, payload.model_dump(exclude_unset=True))

@event_router.delete("/{item_id}")
async def delete_event(item_id: UUID, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    await event_service.delete_event(session, item_id)
    return {"message": "Deleted successfully"}

academic_calendar_router = APIRouter()


@academic_calendar_router.post("", response_model=AcademicCalendarResponse, status_code=status.HTTP_201_CREATED)
async def create_calendar_entry(payload: AcademicCalendarCreate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    return await academic_calendar_service.create_calendar_entry(session, payload.model_dump())

@academic_calendar_router.get("", response_model=list[AcademicCalendarResponse])
async def get_calendar_entries(session: AsyncSession = Depends(get_db)): return await academic_calendar_service.get_calendar_entries(session)

@academic_calendar_router.get("/month/{year}/{month}", response_model=list[AcademicCalendarResponse])
async def get_calendar_entries_by_month(year: int, month: int, session: AsyncSession = Depends(get_db)): return await academic_calendar_service.get_by_month(session, year, month)

@academic_calendar_router.get("/holidays", response_model=list[AcademicCalendarResponse])
async def get_holidays(session: AsyncSession = Depends(get_db)): return await academic_calendar_service.get_holidays(session)

@academic_calendar_router.get("/{item_id}", response_model=AcademicCalendarResponse)
async def get_calendar_entry(item_id: UUID, session: AsyncSession = Depends(get_db)): return await academic_calendar_service.get_calendar_entry(session, item_id)

@academic_calendar_router.put("/{item_id}", response_model=AcademicCalendarResponse)
async def update_calendar_entry(item_id: UUID, payload: AcademicCalendarUpdate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    return await academic_calendar_service.update_calendar_entry(session, item_id, payload.model_dump(exclude_unset=True))

@academic_calendar_router.delete("/{item_id}")
async def delete_calendar_entry(item_id: UUID, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    await academic_calendar_service.delete_calendar_entry(session, item_id)
    return {"message": "Deleted successfully"}
