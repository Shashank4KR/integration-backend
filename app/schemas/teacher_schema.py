from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.base import BaseSchema


class TeacherCreate(BaseSchema):
    user_id: UUID
    employee_id: str = Field(..., min_length=1, max_length=50)
    qualification: Optional[str] = Field(None, max_length=255)
    department_id: Optional[UUID] = None
    join_date: Optional[date] = None
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


class TeacherUpdate(BaseSchema):
    user_id: Optional[UUID] = None
    employee_id: Optional[str] = Field(None, min_length=1, max_length=50)
    qualification: Optional[str] = Field(None, max_length=255)
    department_id: Optional[UUID] = None
    join_date: Optional[date] = None
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


class TeacherResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    employee_id: str
    qualification: Optional[str] = None
    department_id: Optional[UUID] = None
    join_date: Optional[date] = None
    phone: Optional[str] = None
    address: Optional[str] = None
