from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SubjectCreate(BaseModel):
    subject_code: str = Field(..., min_length=1, max_length=50)
    subject_name: str = Field(..., min_length=1, max_length=255)
    department_id: Optional[UUID] = None
    subject_type: Optional[str] = Field(default="THEORY", max_length=50)
    credits: Optional[int] = Field(default=3, ge=0, le=20)
    periods_per_week: Optional[int] = Field(default=4, ge=0, le=40)
    status: Optional[str] = Field(default="ACTIVE", max_length=20)


class SubjectUpdate(BaseModel):
    subject_code: Optional[str] = Field(None, min_length=1, max_length=50)
    subject_name: Optional[str] = Field(None, min_length=1, max_length=255)
    department_id: Optional[UUID] = None
    subject_type: Optional[str] = Field(default=None, max_length=50)
    credits: Optional[int] = Field(default=None, ge=0, le=20)
    periods_per_week: Optional[int] = Field(default=None, ge=0, le=40)
    status: Optional[str] = Field(default=None, max_length=20)


class SubjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subject_code: str
    subject_name: str
    department_id: Optional[UUID] = None
    subject_type: Optional[str] = "THEORY"
    credits: Optional[int] = 3
    periods_per_week: Optional[int] = 4
    status: Optional[str] = "ACTIVE"
    created_at: datetime
    updated_at: datetime
