from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.attendance_model import AttendanceStatus


class AttendanceCreate(BaseModel):
    student_id: UUID
    class_id: UUID
    subject_id: UUID
    teacher_id: UUID
    attendance_date: date
    period_no: int = Field(..., ge=1)
    status: AttendanceStatus
    marked_by: UUID


class AttendanceUpdate(BaseModel):
    status: AttendanceStatus


class AttendanceAuditOverride(BaseModel):
    status: AttendanceStatus
    reason: str = Field(..., min_length=10, description="Mandatory audit justification")


class AttendanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    class_id: UUID
    subject_id: UUID
    teacher_id: UUID
    attendance_date: date
    period_no: int
    status: AttendanceStatus
    marked_by: UUID
    created_at: datetime
    updated_at: datetime


class BulkAttendanceRecord(BaseModel):
    student_id: UUID
    status: str


class BulkAttendanceCreate(BaseModel):
    class_id: UUID
    subject_id: UUID
    teacher_id: UUID
    attendance_date: date
    period_no: int = Field(..., ge=1)
    marked_by: UUID
    records: list[BulkAttendanceRecord]


class StudentAttendanceReport(BaseModel):
    student_id: UUID
    records: list[AttendanceResponse]


class StudentAttendanceSummary(BaseModel):
    student_id: UUID
    total_classes: int
    present: int
    absent: int
    late: int
    attendance_percentage: float


class AttendanceSummary(BaseModel):
    total_records: int
    present: int
    absent: int
    late: int


class ClassAttendanceSummary(BaseModel):
    class_id: UUID
    total_students: int
    present: int
    absent: int
    late: int


class SubjectAttendanceSummary(AttendanceSummary):
    subject_id: UUID


class TeacherAttendanceSummary(AttendanceSummary):
    teacher_id: UUID
