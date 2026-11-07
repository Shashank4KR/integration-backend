from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ClassSubjectCreate(BaseModel):
    class_id: UUID
    subject_id: UUID


class ClassSubjectUpdate(BaseModel):
    class_id: UUID | None = None
    subject_id: UUID | None = None


class ClassSubjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    class_id: UUID
    subject_id: UUID
    created_at: datetime
