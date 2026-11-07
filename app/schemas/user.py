from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer, field_validator

from app.schemas.base import BaseSchema


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role_name: str
    description: str | None = None

    @field_serializer("id")
    def serialize_role_id(self, value: UUID) -> str:
        return f"{value.int & 0xffff:04d}"


class UserCreate(BaseSchema):
    username: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    phone: str | None = Field(None, max_length=20)
    status: bool = True
    role_id: str = Field(..., min_length=4, max_length=36)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if not v:
            return None
        cleaned = "".join(ch for ch in v if ch.isdigit())
        if not cleaned:
            raise ValueError("Phone number must contain only numeric digits (0-9)")
        return cleaned


class UserUpdate(BaseSchema):
    username: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    phone: str | None = Field(None, max_length=20)
    avatar_url: str | None = None
    status: bool | None = None
    role_id: str | None = Field(default=None, min_length=4, max_length=36)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if not v:
            return None
        cleaned = "".join(ch for ch in v if ch.isdigit())
        if not cleaned:
            raise ValueError("Phone number must contain only numeric digits (0-9)")
        return cleaned


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: EmailStr
    phone: str | None = None
    avatar_url: str | None = None
    status: bool
    last_login: datetime | None = None
    must_change_password: bool = False
    role_id: UUID
    role: RoleResponse | None = None
    created_at: datetime
    updated_at: datetime | None = None

    @field_serializer("role_id")
    def serialize_role_id(self, value: UUID) -> str:
        return f"{value.int & 0xffff:04d}"


class UserCreateResponse(UserResponse):
    created_id: UUID | None = None
    message: str = "User created successfully"
