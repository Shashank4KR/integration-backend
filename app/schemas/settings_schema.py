from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import ConfigDict, EmailStr, Field, model_validator
from app.schemas.base import BaseSchema, ResponseSchema


class SettingsCategoryResponse(ResponseSchema):
    id: UUID | None = None
    category: str
    config: dict[str, Any]
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CategorySettingsUpdate(BaseSchema):
    config: dict[str, Any] = Field(default_factory=dict)


class SystemSettingsBulkUpdate(BaseSchema):
    settings: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def normalize_input(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "settings" in data and isinstance(data["settings"], dict):
                return data
            return {"settings": data}
        return data


class ProfileUpdateRequest(BaseSchema):
    username: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=20, pattern=r"^\+?[0-9\s\-]+$")
    avatar_url: str | None = Field(None, max_length=4_000_000)


class ChangePasswordRequest(BaseSchema):
    current_password: str = Field(..., min_length=1, max_length=255)
    new_password: str = Field(..., min_length=1, max_length=128)
    confirm_password: str | None = Field(None, max_length=128)


class SessionRecordResponse(ResponseSchema):
    id: UUID
    user_id: UUID
    login_time: datetime
    logout_time: datetime | None = None
    device: str | None = None
    ip_address: str | None = None
    is_active: bool = False
