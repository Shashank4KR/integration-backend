from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LoginHistoryCreate(BaseModel):
    user_id: UUID
    login_time: datetime | None = None
    device: str | None = Field(None, max_length=255)
    ip_address: str | None = Field(None, max_length=64)


class LoginHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    login_time: datetime
    logout_time: datetime | None
    device: str | None
    ip_address: str | None
    duration_minutes: int | None
    created_at: datetime
    updated_at: datetime


class AuditLogCreate(BaseModel):
    user_id: UUID
    activity: str = Field(min_length=1, max_length=255)
    activity_time: datetime | None = None
    details: str | None = None


class AuditLogUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    username: str
    email: str | None = None


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    activity: str
    activity_time: datetime
    details: str | None
    created_at: datetime
    updated_at: datetime
    user: AuditLogUser | None = None

