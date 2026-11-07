from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_serializer, field_validator


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role_name: str
    description: Optional[str] = None

    @field_serializer("id")
    def serialize_role_id(self, value: UUID) -> str:
        return f"{value.int & 0xffff:04d}"


class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    phone: Optional[str] = Field(None, max_length=20)
    status: bool = True
    role_id: str = Field(..., min_length=4, max_length=36)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        cleaned = "".join(ch for ch in v if ch.isdigit())
        if not cleaned:
            raise ValueError("Phone number must contain only numeric digits (0-9)")
        return cleaned


class UserUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)
    phone: Optional[str] = Field(None, max_length=20)
    avatar_url: Optional[str] = None
    status: Optional[bool] = None
    role_id: Optional[str] = Field(default=None, min_length=4, max_length=36)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
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
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    status: bool
    last_login: Optional[datetime] = None
    must_change_password: bool = False
    role_id: UUID
    role: Optional[RoleResponse] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    @field_serializer("role_id")
    def serialize_role_id(self, value: UUID) -> str:
        return f"{value.int & 0xffff:04d}"


class UserCreateResponse(UserResponse):
    created_id: Optional[UUID] = None
    message: str = "User created successfully"
