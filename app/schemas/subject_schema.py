from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SubjectCreate(BaseModel):
    subject_code: str = Field(..., min_length=1, max_length=50)
    subject_name: str = Field(..., min_length=1, max_length=255)
    department_id: Optional[UUID] = None


class SubjectUpdate(BaseModel):
    subject_code: Optional[str] = Field(None, min_length=1, max_length=50)
    subject_name: Optional[str] = Field(None, min_length=1, max_length=255)
    department_id: Optional[UUID] = None


class SubjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subject_code: str
    subject_name: str
    department_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
