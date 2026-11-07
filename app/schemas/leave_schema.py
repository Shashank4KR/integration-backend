from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models.leave_model import LeaveStatus


class LeaveTypeCreate(BaseModel):
    leave_type_name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class LeaveTypeUpdate(BaseModel):
    leave_type_name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None


class LeaveTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    leave_type_name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class LeaveRequestCreate(BaseModel):
    user_id: UUID
    leave_type_id: UUID
    from_date: date
    to_date: date
    reason: str = Field(..., min_length=1)


class LeaveRequestUpdate(BaseModel):
    leave_type_id: UUID | None = None
    from_date: date | None = None
    to_date: date | None = None
    reason: str | None = Field(None, min_length=1)


class LeaveApprovalRequest(BaseModel):
    remarks: str | None = None


class LeaveRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    leave_type_id: UUID
    from_date: date
    to_date: date
    reason: str
    status: LeaveStatus
    applied_on: datetime
    approved_by: UUID | None = None
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def total_days(self) -> int:
        return (self.to_date - self.from_date).days + 1


class LeaveSummaryResponse(BaseModel):
    total_requests: int
    pending: int
    approved: int
    rejected: int
    cancelled: int
