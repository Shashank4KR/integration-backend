from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.base import BaseSchema


class ClassCreate(BaseSchema):
    class_name: str = Field(..., min_length=1, max_length=100)
    section: str = Field(..., min_length=1, max_length=50)
    academic_year: str = Field(..., min_length=1, max_length=20)
    class_teacher_id: UUID | None = None
    room_number: str | None = Field(None, max_length=50)
    status: str | None = Field("ACTIVE", max_length=20)


class ClassUpdate(BaseSchema):
    class_name: str | None = Field(None, min_length=1, max_length=100)
    section: str | None = Field(None, min_length=1, max_length=50)
    academic_year: str | None = Field(None, min_length=1, max_length=20)
    class_teacher_id: UUID | None = None
    room_number: str | None = Field(None, max_length=50)
    status: str | None = Field(None, max_length=20)


class ClassResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    class_name: str
    section: str
    academic_year: str
    class_teacher_id: UUID | None = None
    room_number: str | None = None
    status: str | None = "ACTIVE"
    created_at: datetime
    updated_at: datetime


class ClassSubjectSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subject_name: str


class ClassTeacherSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: str
