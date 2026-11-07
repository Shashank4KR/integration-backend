from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AdminCreate(BaseModel):
    user_id: UUID
    admin_name: str = Field(..., min_length=1, max_length=255)
    phone: str | None = Field(None, max_length=20)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if not v:
            return None
        cleaned = "".join(ch for ch in v if ch.isdigit())
        if not cleaned:
            raise ValueError("Phone number must contain only numeric digits (0-9)")
        return cleaned


class AdminUpdate(BaseModel):
    user_id: UUID | None = None
    admin_name: str | None = Field(None, min_length=1, max_length=255)
    phone: str | None = Field(None, max_length=20)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if not v:
            return None
        cleaned = "".join(ch for ch in v if ch.isdigit())
        if not cleaned:
            raise ValueError("Phone number must contain only numeric digits (0-9)")
        return cleaned


class AdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    admin_name: str
    phone: str | None = None
