from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TeacherSubjectCreate(BaseModel):
    teacher_id: UUID
    subject_id: UUID
    class_id: UUID


class TeacherSubjectUpdate(BaseModel):
    teacher_id: UUID | None = None
    subject_id: UUID | None = None
    class_id: UUID | None = None


class TeacherSubjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    teacher_id: UUID
    subject_id: UUID
    class_id: UUID
    created_at: datetime
