from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.base import BaseSchema


class TeacherCreate(BaseSchema):
    user_id: UUID
    employee_id: str = Field(..., min_length=1, max_length=50)
    qualification: str | None = Field(None, max_length=255)
    department_id: UUID | None = None
    join_date: date | None = None
    phone: str | None = Field(None, max_length=20)
    address: str | None = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if not v:
            return None
        cleaned = "".join(ch for ch in v if ch.isdigit())
        if not cleaned:
            raise ValueError("Phone number must contain only numeric digits (0-9)")
        return cleaned


class TeacherUpdate(BaseSchema):
    user_id: UUID | None = None
    employee_id: str | None = Field(None, min_length=1, max_length=50)
    qualification: str | None = Field(None, max_length=255)
    department_id: UUID | None = None
    join_date: date | None = None
    phone: str | None = Field(None, max_length=20)
    address: str | None = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if not v:
            return None
        cleaned = "".join(ch for ch in v if ch.isdigit())
        if not cleaned:
            raise ValueError("Phone number must contain only numeric digits (0-9)")
        return cleaned


class TeacherResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    employee_id: str
    qualification: str | None = None
    department_id: UUID | None = None
    join_date: date | None = None
    phone: str | None = None
    address: str | None = None
