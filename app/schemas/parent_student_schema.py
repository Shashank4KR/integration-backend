from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ParentStudentCreate(BaseModel):
    parent_id: UUID
    student_id: UUID
    relationship: str | None = Field(None, max_length=50)


class ParentStudentUpdate(BaseModel):
    parent_id: UUID | None = None
    student_id: UUID | None = None
    relationship: str | None = Field(None, max_length=50)


class ParentStudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    parent_id: UUID
    student_id: UUID
    relationship: str | None = None
