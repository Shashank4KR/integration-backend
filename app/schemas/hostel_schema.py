from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.hostel_model import HostelAllocationStatus, HostelBedStatus, HostelBlockStatus, HostelRoomStatus


class HostelBlockCreate(BaseModel):
    block_name: str
    block_type: str
    total_floors: int = Field(gt=0)
    total_rooms: int = Field(gt=0)
    warden_id: UUID | None = None
    status: HostelBlockStatus = HostelBlockStatus.ACTIVE


class HostelBlockUpdate(BaseModel):
    block_name: str | None = None
    block_type: str | None = None
    total_floors: int | None = Field(default=None, gt=0)
    total_rooms: int | None = Field(default=None, gt=0)
    warden_id: UUID | None = None
    status: HostelBlockStatus | None = None


class HostelBlockResponse(HostelBlockCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime


class HostelRoomCreate(BaseModel):
    block_id: UUID
    room_no: str
    floor_no: int = Field(ge=0)
    capacity: int = Field(gt=0)
    status: HostelRoomStatus = HostelRoomStatus.AVAILABLE


class HostelRoomUpdate(BaseModel):
    room_no: str | None = None
    floor_no: int | None = Field(default=None, ge=0)
    capacity: int | None = Field(default=None, gt=0)
    status: HostelRoomStatus | None = None


class HostelRoomResponse(HostelRoomCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    occupancy: int
    created_at: datetime
    updated_at: datetime


class HostelBedCreate(BaseModel):
    room_id: UUID
    bed_no: str
    status: HostelBedStatus = HostelBedStatus.VACANT


class HostelBedUpdate(BaseModel):
    bed_no: str | None = None
    status: HostelBedStatus | None = None


class HostelBedResponse(HostelBedCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime


class HostelAllocationCreate(BaseModel):
    student_id: UUID
    bed_id: UUID
    check_in_date: date


class HostelAllocationResponse(HostelAllocationCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    check_out_date: date | None
    status: HostelAllocationStatus
    created_at: datetime
    updated_at: datetime
    bed_no: str | None = None
    room_no: str | None = None
    block_name: str | None = None
    floor_no: int | None = None


class HostelTransferRequest(BaseModel):
    bed_id: UUID
    check_in_date: date


class HostelCheckoutRequest(BaseModel):
    checkout_date: date

