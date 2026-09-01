from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class AssignmentCreate(BaseModel):
    teacher_id: UUID
    class_id: UUID
    subject_id: UUID
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    due_date: datetime
    attachment: str | None = Field(None, max_length=500)


class AssignmentUpdate(BaseModel):
    teacher_id: UUID | None = None
    class_id: UUID | None = None
    subject_id: UUID | None = None
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    due_date: datetime | None = None
    attachment: str | None = Field(None, max_length=500)


class AssignmentResponse(AssignmentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime
    class_name: str | None = None
    subject_name: str | None = None


class AssignmentSubmissionCreate(BaseModel):
    assignment_id: UUID
    student_id: UUID
    submitted_on: datetime | None = None
    file_path: str | None = Field(None, max_length=500)
    marks: Decimal | None = Field(None, ge=0)
    remarks: str | None = None


class AssignmentSubmissionUpdate(BaseModel):
    submitted_on: datetime | None = None
    file_path: str | None = Field(None, max_length=500)
    marks: Decimal | None = Field(None, ge=0)
    remarks: str | None = None


class AssignmentSubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    assignment_id: UUID
    student_id: UUID
    submitted_on: datetime
    file_path: str | None
    marks: Decimal | None
    remarks: str | None
    created_at: datetime
    updated_at: datetime
    student_name: str | None = None


class AssignmentSummaryResponse(BaseModel):
    assignment_id: UUID
    total_students: int
    submitted: int
    pending: int
