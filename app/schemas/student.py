from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.base import BaseSchema


class StudentBase(BaseSchema):
    admission_no: str = Field(..., min_length=1, max_length=50)
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    gender: str | None = Field(None, max_length=20)
    blood_group: str | None = Field(None, max_length=10)
    class_name: str | None = Field(None, max_length=100)
    class_id: UUID | None = None
    roll_no: str | None = Field(None, max_length=50)
    joining_date: date | None = None
    photo: str | None = Field(None, max_length=500)


class StudentCreate(StudentBase):
    user_id: UUID


class StudentUpdate(BaseSchema):
    user_id: UUID | None = None
    admission_no: str | None = Field(None, min_length=1, max_length=50)
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    gender: str | None = Field(None, max_length=20)
    blood_group: str | None = Field(None, max_length=10)
    class_name: str | None = Field(None, max_length=100)
    class_id: UUID | None = None
    roll_no: str | None = Field(None, max_length=50)
    joining_date: date | None = None
    photo: str | None = Field(None, max_length=500)


class StudentResponse(StudentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
