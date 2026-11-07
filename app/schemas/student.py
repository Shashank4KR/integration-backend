from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from app.schemas.base import BaseSchema


class StudentBase(BaseSchema):
    admission_no: str = Field(..., min_length=1, max_length=50)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[str] = Field(None, max_length=20)
    blood_group: Optional[str] = Field(None, max_length=10)
    class_name: Optional[str] = Field(None, max_length=100)
    class_id: Optional[UUID] = None
    roll_no: Optional[str] = Field(None, max_length=50)
    joining_date: Optional[date] = None
    photo: Optional[str] = Field(None, max_length=500)


class StudentCreate(StudentBase):
    user_id: UUID


class StudentUpdate(BaseSchema):
    user_id: Optional[UUID] = None
    admission_no: Optional[str] = Field(None, min_length=1, max_length=50)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[str] = Field(None, max_length=20)
    blood_group: Optional[str] = Field(None, max_length=10)
    class_name: Optional[str] = Field(None, max_length=100)
    class_id: Optional[UUID] = None
    roll_no: Optional[str] = Field(None, max_length=50)
    joining_date: Optional[date] = None
    photo: Optional[str] = Field(None, max_length=500)


class StudentResponse(StudentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
