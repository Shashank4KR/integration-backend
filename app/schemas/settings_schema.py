from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SettingsCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID | None = None
    category: str
    config: dict[str, Any]
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CategorySettingsUpdate(BaseModel):
    config: dict[str, Any] = Field(default_factory=dict)


class SystemSettingsBulkUpdate(BaseModel):
    settings: dict[str, dict[str, Any]] = Field(default_factory=dict)


class ProfileUpdateRequest(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    avatar_url: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)
    confirm_password: str | None = None


class SessionRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    login_time: datetime
    logout_time: datetime | None = None
    device: str | None = None
    ip_address: str | None = None
    is_active: bool = False
