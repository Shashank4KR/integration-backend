from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.base import BaseSchema


class ParentBase(BaseSchema):
    occupation: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        cleaned = "".join(ch for ch in v if ch.isdigit())
        if not cleaned:
            raise ValueError("Phone number must contain only numeric digits (0-9)")
        return cleaned


class ParentCreate(ParentBase):
    user_id: UUID


class ParentUpdate(BaseSchema):
    user_id: Optional[UUID] = None
    occupation: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        cleaned = "".join(ch for ch in v if ch.isdigit())
        if not cleaned:
            raise ValueError("Phone number must contain only numeric digits (0-9)")
        return cleaned


class ParentResponse(ParentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
