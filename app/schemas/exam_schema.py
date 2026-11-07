from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ExamCreate(BaseModel):
    exam_name: str = Field(..., min_length=1, max_length=255)
    exam_type: str = Field(..., min_length=1, max_length=100)
    class_id: UUID
    start_date: date
    end_date: date
    max_marks: int = Field(..., gt=0)


class ExamUpdate(BaseModel):
    exam_name: str | None = Field(None, min_length=1, max_length=255)
    exam_type: str | None = Field(None, min_length=1, max_length=100)
    class_id: UUID | None = None
    start_date: date | None = None
    end_date: date | None = None
    max_marks: int | None = Field(None, gt=0)


class ExamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    exam_name: str
    exam_type: str
    class_id: UUID
    class_name: str | None = None
    section: str | None = None
    start_date: date
    end_date: date
    max_marks: int
    created_at: datetime
    updated_at: datetime



class ExamResultCreate(BaseModel):
    exam_id: UUID
    student_id: UUID
    subject_id: UUID
    marks_obtained: Decimal = Field(..., ge=0)
    remarks: str | None = None


class ExamResultUpdate(BaseModel):
    marks_obtained: Decimal | None = Field(None, ge=0)
    remarks: str | None = None


class ExamResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    exam_id: UUID
    student_id: UUID
    subject_id: UUID
    marks_obtained: Decimal
    grade: str | None = None
    remarks: str | None = None
    entered_by: UUID | None = None
    created_at: datetime
    updated_at: datetime


class ExamResultAuditOverride(BaseModel):
    marks_obtained: Decimal = Field(..., ge=0)
    remarks: str | None = None
    reason: str = Field(..., min_length=10, description="Mandatory audit justification")


class ReportCardGenerate(BaseModel):
    student_id: UUID
    exam_id: UUID
    remarks: str | None = None


class ReportCardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    exam_id: UUID
    total_marks: Decimal
    obtained_marks: Decimal
    percentage: Decimal
    rank: int | None = None
    result: str
    remarks: str | None = None
    created_at: datetime
    updated_at: datetime


class ExamTopperResponse(BaseModel):
    rank: int
    student_name: str
    percentage: Decimal


class StudentPerformanceSummary(BaseModel):
    student_id: UUID
    total_exams: int
    average_percentage: float
    best_subject: str | None = None
    worst_subject: str | None = None


class ExamSubjectCreate(BaseModel):
    subject_id: UUID


class ExamSubjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    exam_id: UUID
    subject_id: UUID
    created_at: datetime


class ExamInvigilatorCreate(BaseModel):
    teacher_id: UUID
    room_no: str | None = None
    invigilator_date: date | None = None


class ExamInvigilatorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    exam_id: UUID
    teacher_id: UUID
    room_no: str | None = None
    invigilator_date: date | None = None
    created_at: datetime


from datetime import time


class ExamTimetableCreate(BaseModel):
    subject_id: UUID
    exam_date: date
    start_time: time
    end_time: time
    room_no: str | None = None


class ExamTimetableResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    exam_id: UUID
    subject_id: UUID
    exam_date: date
    start_time: time
    end_time: time
    room_no: str | None = None
    created_at: datetime

