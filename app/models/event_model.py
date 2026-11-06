import uuid
from datetime import date, datetime
from enum import Enum

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EventType(str, Enum):
    ACADEMIC = "ACADEMIC"
    SPORTS = "SPORTS"
    CULTURAL = "CULTURAL"
    EXAMINATION = "EXAMINATION"
    MEETING = "MEETING"
    HOLIDAY = "HOLIDAY"
    COMPETITION = "COMPETITION"
    CELEBRATION = "CELEBRATION"
    WORKSHOP = "WORKSHOP"
    OTHER = "OTHER"


class AcademicCalendarEventType(str, Enum):
    SEMESTER_START = "SEMESTER_START"
    SEMESTER_END = "SEMESTER_END"
    EXAM = "EXAM"
    HOLIDAY = "HOLIDAY"
    ADMISSION = "ADMISSION"
    REGISTRATION = "REGISTRATION"
    EVENT = "EVENT"
    OTHER = "OTHER"


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_name: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    venue: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    creator: Mapped["User"] = relationship("User", back_populates="events_created", foreign_keys=[created_by], lazy="selectin")


class AcademicCalendar(Base):
    __tablename__ = "academic_calendar"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_holiday: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
