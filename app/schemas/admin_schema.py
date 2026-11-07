from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AdminCreate(BaseModel):
    user_id: UUID
    admin_name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        cleaned = "".join(ch for ch in v if ch.isdigit())
        if not cleaned:
            raise ValueError("Phone number must contain only numeric digits (0-9)")
        return cleaned


class AdminUpdate(BaseModel):
    user_id: Optional[UUID] = None
    admin_name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
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
    phone: Optional[str] = None
