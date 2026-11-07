from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.base import BaseSchema, ResponseSchema


class BusCreate(BaseSchema):
    bus_number: str = Field(..., min_length=1, max_length=50)
    model: str = Field(..., min_length=1, max_length=100)
    capacity: int = Field(..., ge=1, le=200)


class BusUpdate(BaseSchema):
    bus_number: str | None = Field(None, min_length=1, max_length=50)
    model: str | None = Field(None, min_length=1, max_length=100)
    capacity: int | None = Field(None, ge=1, le=200)


class BusResponse(ResponseSchema):
    id: UUID
    bus_number: str
    model: str
    capacity: int
    created_at: datetime
    updated_at: datetime


class RouteStopCreate(BaseSchema):
    stop_name: str
    stop_order: int = 1
    pickup_time: str | None = None


class RouteStopResponse(RouteStopCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    route_id: UUID
    created_at: datetime
    updated_at: datetime


class RouteCreate(BaseSchema):
    route_name: str
    start_point: str
    end_point: str
    stops: list[RouteStopCreate] | None = []


class RouteUpdate(BaseSchema):
    route_name: str | None = None
    start_point: str | None = None
    end_point: str | None = None
    stops: list[RouteStopCreate] | None = None


class RouteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    route_name: str
    start_point: str
    end_point: str
    stops: list[RouteStopResponse] = []
    created_at: datetime
    updated_at: datetime


class StudentTransportCreate(BaseSchema):
    student_id: UUID
    bus_id: UUID
    route_id: UUID
    stop_point: str


class StudentTransportUpdate(BaseSchema):
    student_id: UUID | None = None
    bus_id: UUID | None = None
    route_id: UUID | None = None
    stop_point: str | None = None


class StudentTransportResponse(ResponseSchema):
    id: UUID
    student_id: UUID
    bus_id: UUID
    route_id: UUID
    stop_point: str
    created_at: datetime
    updated_at: datetime


class DriverCreate(BaseSchema):
    driver_name: str
    license_number: str
    phone: str | None = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if not v:
            return None
        cleaned = "".join(ch for ch in v if ch.isdigit())
        if not cleaned:
            raise ValueError("Phone number must contain only numeric digits (0-9)")
        return cleaned
    experience: int | None = None
    bus_id: UUID | None = None
    status: str = "ACTIVE"


class DriverUpdate(BaseSchema):
    driver_name: str | None = None
    license_number: str | None = None
    phone: str | None = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if not v:
            return None
        cleaned = "".join(ch for ch in v if ch.isdigit())
        if not cleaned:
            raise ValueError("Phone number must contain only numeric digits (0-9)")
        return cleaned
    experience: int | None = None
    bus_id: UUID | None = None
    status: str | None = None


class DriverResponse(ResponseSchema):
    id: UUID
    driver_name: str
    license_number: str
    phone: str | None = None
    experience: int | None = None
    bus_id: UUID | None = None
    status: str
    created_at: datetime
    updated_at: datetime
