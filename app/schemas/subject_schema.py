from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.base import BaseSchema


class SubjectCreate(BaseSchema):
    subject_code: str = Field(..., min_length=1, max_length=50)
    subject_name: str = Field(..., min_length=1, max_length=255)
    department_id: UUID | None = None
    subject_type: str | None = Field(default="THEORY", max_length=50)
    credits: int | None = Field(default=3, ge=0, le=20)
    periods_per_week: int | None = Field(default=4, ge=0, le=40)
    status: str | None = Field(default="ACTIVE", max_length=20)


class SubjectUpdate(BaseSchema):
    subject_code: str | None = Field(None, min_length=1, max_length=50)
    subject_name: str | None = Field(None, min_length=1, max_length=255)
    department_id: UUID | None = None
    subject_type: str | None = Field(default=None, max_length=50)
    credits: int | None = Field(default=None, ge=0, le=20)
    periods_per_week: int | None = Field(default=None, ge=0, le=40)
    status: str | None = Field(default=None, max_length=20)


class SubjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subject_code: str
    subject_name: str
    department_id: UUID | None = None
    subject_type: str | None = "THEORY"
    credits: int | None = 3
    periods_per_week: int | None = 4
    status: str | None = "ACTIVE"
    created_at: datetime
    updated_at: datetime
