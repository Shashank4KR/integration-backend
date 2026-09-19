from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BusCreate(BaseModel):
    bus_number: str
    model: str
    capacity: int


class BusUpdate(BaseModel):
    bus_number: str | None = None
    model: str | None = None
    capacity: int | None = None


class BusResponse(BusCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime


class RouteStopCreate(BaseModel):
    stop_name: str
    stop_order: int = 1
    pickup_time: str | None = None


class RouteStopResponse(RouteStopCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    route_id: UUID
    created_at: datetime
    updated_at: datetime


class RouteCreate(BaseModel):
    route_name: str
    start_point: str
    end_point: str
    stops: list[RouteStopCreate] | None = []


class RouteUpdate(BaseModel):
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


class StudentTransportCreate(BaseModel):
    student_id: UUID
    bus_id: UUID
    route_id: UUID
    stop_point: str


class StudentTransportUpdate(BaseModel):
    student_id: UUID | None = None
    bus_id: UUID | None = None
    route_id: UUID | None = None
    stop_point: str | None = None


class StudentTransportResponse(StudentTransportCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime


class DriverCreate(BaseModel):
    driver_name: str
    license_number: str
    phone: str | None = None
    experience: int | None = None
    bus_id: UUID | None = None
    status: str = "ACTIVE"


class DriverUpdate(BaseModel):
    driver_name: str | None = None
    license_number: str | None = None
    phone: str | None = None
    experience: int | None = None
    bus_id: UUID | None = None
    status: str | None = None


class DriverResponse(DriverCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime
