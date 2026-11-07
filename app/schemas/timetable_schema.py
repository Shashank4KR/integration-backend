from datetime import datetime, time
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TimetableCreate(BaseModel):
    class_id: UUID
    subject_id: UUID
    teacher_id: UUID
    day_of_week: str = Field(..., min_length=1, max_length=20)
    start_time: time
    end_time: time
    room_no: str | None = Field(None, max_length=50)
    period_no: int | None = None

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class TimetableUpdate(BaseModel):
    class_id: UUID | None = None
    subject_id: UUID | None = None
    teacher_id: UUID | None = None
    day_of_week: str | None = Field(None, min_length=1, max_length=20)
    start_time: time | None = None
    end_time: time | None = None
    room_no: str | None = Field(None, max_length=50)
    period_no: int | None = None


class TimetableResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    class_id: UUID
    subject_id: UUID
    teacher_id: UUID
    day_of_week: str
    start_time: time
    end_time: time
    room_no: str | None = None
    period_no: int | None = None
    created_at: datetime
    updated_at: datetime
