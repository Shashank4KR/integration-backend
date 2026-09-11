import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class HostelBlockStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class HostelRoomStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    FULL = "FULL"
    MAINTENANCE = "MAINTENANCE"


class HostelBedStatus(str, enum.Enum):
    VACANT = "VACANT"
    OCCUPIED = "OCCUPIED"
    RESERVED = "RESERVED"


class HostelAllocationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    TRANSFERRED = "TRANSFERRED"
    CHECKED_OUT = "CHECKED_OUT"


class HostelBlock(Base):
    __tablename__ = "hostel_blocks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    block_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    block_type: Mapped[str] = mapped_column(String(100), nullable=False)
    total_floors: Mapped[int] = mapped_column(Integer, nullable=False)
    total_rooms: Mapped[int] = mapped_column(Integer, nullable=False)
    warden_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status: Mapped[HostelBlockStatus] = mapped_column(String(20), default=HostelBlockStatus.ACTIVE, server_default=HostelBlockStatus.ACTIVE.value, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    warden = relationship("User", back_populates="hostel_blocks", foreign_keys=[warden_id], lazy="selectin")
    rooms: Mapped[list["HostelRoom"]] = relationship("HostelRoom", back_populates="block")


class HostelRoom(Base):
    __tablename__ = "hostel_rooms"
    __table_args__ = (UniqueConstraint("block_id", "room_no", name="uq_hostel_rooms_block_room_no"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    block_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("hostel_blocks.id"), nullable=False)
    room_no: Mapped[str] = mapped_column(String(100), nullable=False)
    floor_no: Mapped[int] = mapped_column(Integer, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    occupancy: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    status: Mapped[HostelRoomStatus] = mapped_column(String(20), default=HostelRoomStatus.AVAILABLE, server_default=HostelRoomStatus.AVAILABLE.value, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    block: Mapped[HostelBlock] = relationship("HostelBlock", back_populates="rooms", lazy="selectin")
    beds: Mapped[list["HostelBed"]] = relationship("HostelBed", back_populates="room")


class HostelBed(Base):
    __tablename__ = "hostel_beds"
    __table_args__ = (UniqueConstraint("room_id", "bed_no", name="uq_hostel_beds_room_bed_no"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("hostel_rooms.id"), nullable=False)
    bed_no: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[HostelBedStatus] = mapped_column(String(20), default=HostelBedStatus.VACANT, server_default=HostelBedStatus.VACANT.value, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    room: Mapped[HostelRoom] = relationship("HostelRoom", back_populates="beds", lazy="selectin")
    allocations: Mapped[list["HostelAllocation"]] = relationship("HostelAllocation", back_populates="bed")


class HostelAllocation(Base):
    __tablename__ = "hostel_allocations"
    __table_args__ = (
        Index("uq_hostel_allocations_active_student", "student_id", unique=True, postgresql_where=text("status = 'ACTIVE'")),
        Index("uq_hostel_allocations_active_bed", "bed_id", unique=True, postgresql_where=text("status = 'ACTIVE'")),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    bed_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("hostel_beds.id"), nullable=False)
    check_in_date: Mapped[date] = mapped_column(Date, nullable=False)
    check_out_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[HostelAllocationStatus] = mapped_column(String(20), default=HostelAllocationStatus.ACTIVE, server_default=HostelAllocationStatus.ACTIVE.value, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    student = relationship("Student", back_populates="hostel_allocations", lazy="selectin")
    bed: Mapped[HostelBed] = relationship("HostelBed", back_populates="allocations", lazy="selectin")
    leave_requests: Mapped[list["HostelLeaveRequest"]] = relationship("HostelLeaveRequest", back_populates="allocation", lazy="selectin")

    @property
    def bed_no(self) -> str | None:
        return self.bed.bed_no if self.bed else None

    @property
    def room_no(self) -> str | None:
        return self.bed.room.room_no if self.bed and self.bed.room else None

    @property
    def floor_no(self) -> int | None:
        return self.bed.room.floor_no if self.bed and self.bed.room else None

    @property
    def block_name(self) -> str | None:
        return self.bed.room.block.block_name if self.bed and self.bed.room and self.bed.room.block else None
