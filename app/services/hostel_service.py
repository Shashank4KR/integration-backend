from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hostel_model import HostelAllocation, HostelAllocationStatus, HostelBed, HostelBedStatus, HostelBlock, HostelRoom, HostelRoomStatus
from app.models.student_model import Student
from app.models.user import User
from app.repositories.hostel_repository import hostel_allocation_repository, hostel_bed_repository, hostel_block_repository, hostel_room_repository
from app.services.crud_service import CRUDService


def _bad_request(detail: str) -> None:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class HostelBlockService(CRUDService):
    async def create_block(self, session, data):
        self._validate(data)
        return await self.create(session, data)
    async def update_block(self, session, item_id, data):
        self._validate(data)
        return await self.update(session, item_id, data)
    async def delete_block(self, session, item_id):
        if await self.repository.get_block_rooms(session, item_id): _bad_request("Cannot delete a block that has rooms")
        await self.delete(session, item_id)
    async def get_block(self, session, item_id): return await self.get(session, item_id)
    async def get_blocks(self, session): return await self.list(session)
    def _validate(self, data):
        for field, label in (("block_name", "Block name"), ("block_type", "Block type")):
            if field in data and not data[field].strip(): _bad_request(f"{label} cannot be empty")
        for field, label in (("total_floors", "Total floors"), ("total_rooms", "Total rooms")):
            if field in data and data[field] <= 0: _bad_request(f"{label} must be greater than zero")


class HostelRoomService(CRUDService):
    async def create_room(self, session, data):
        self._validate(data)
        room = await self.create(session, data)
        capacity = int(data.get("capacity", 1))
        room_no = data.get("room_no", "Room")
        for i in range(1, capacity + 1):
            bed_no = f"{room_no}-{i}"
            bed = HostelBed(
                room_id=room.id,
                bed_no=bed_no,
                status=HostelBedStatus.VACANT,
            )
            session.add(bed)
        await session.commit()
        await session.refresh(room)
        return room
    async def update_room(self, session, item_id, data):
        room = await self.get(session, item_id)
        self._validate(data)
        if data.get("capacity", room.capacity) < room.occupancy: _bad_request("Capacity cannot be below occupancy")
        return await self.update(session, item_id, data)
    async def delete_room(self, session, item_id):
        if await self.repository.get_room_beds(session, item_id): _bad_request("Cannot delete a room that has beds")
        await self.delete(session, item_id)
    async def get_room(self, session, item_id): return await self.get(session, item_id)
    async def get_rooms(self, session): return await self.list(session)
    def _validate(self, data):
        if "room_no" in data and not data["room_no"].strip(): _bad_request("Room number cannot be empty")
        if "capacity" in data and data["capacity"] <= 0: _bad_request("Capacity must be greater than zero")
        if "floor_no" in data and data["floor_no"] < 0: _bad_request("Floor number cannot be negative")


class HostelBedService(CRUDService):
    async def ensure_room_beds(self, session: AsyncSession):
        rooms = list((await session.execute(select(HostelRoom))).scalars().all())
        created_any = False
        for r in rooms:
            existing_beds = list((await session.execute(select(HostelBed).where(HostelBed.room_id == r.id))).scalars().all())
            existing_nos = {b.bed_no for b in existing_beds}
            for i in range(1, r.capacity + 1):
                bed_no = f"{r.room_no}-{i}"
                if bed_no not in existing_nos:
                    session.add(HostelBed(
                        room_id=r.id,
                        bed_no=bed_no,
                        status=HostelBedStatus.VACANT,
                    ))
                    created_any = True
        if created_any:
            await session.commit()

    async def create_bed(self, session, data):
        if not data["bed_no"].strip(): _bad_request("Bed number cannot be empty")
        if data.get("status") == HostelBedStatus.OCCUPIED: _bad_request("Beds can only be occupied through allocation")
        return await self.create(session, data)
    async def update_bed(self, session, item_id, data):
        bed = await self.get(session, item_id)
        if "bed_no" in data and not data["bed_no"].strip(): _bad_request("Bed number cannot be empty")
        if data.get("status") == HostelBedStatus.OCCUPIED: _bad_request("Beds can only be occupied through allocation")
        if data.get("status") == HostelBedStatus.VACANT and await hostel_allocation_repository.get_bed_allocation(session, bed.id): _bad_request("Cannot vacate a bed with an active allocation")
        return await self.update(session, item_id, data)
    async def delete_bed(self, session, item_id):
        if await session.scalar(select(HostelAllocation.id).where(HostelAllocation.bed_id == item_id).limit(1)):
            _bad_request("Cannot delete a bed with allocation history")
        await self.delete(session, item_id)
    async def get_bed(self, session, item_id): return await self.get(session, item_id)
    async def get_beds(self, session):
        await self.ensure_room_beds(session)
        return await self.list(session)
    async def get_available_beds(self, session):
        await self.ensure_room_beds(session)
        return await self.repository.get_available_beds(session)


class HostelAllocationService(CRUDService):
    async def allocate(self, session: AsyncSession, data: dict):
        if await session.get(Student, data["student_id"]) is None: _bad_request("Student must exist")
        if await self.repository.get_student_allocation(session, data["student_id"]): _bad_request("Student can have only one active hostel allocation")
        bed = await hostel_bed_service.get_bed(session, data["bed_id"])
        if bed.status != HostelBedStatus.VACANT: _bad_request("Bed is not vacant")
        room = await hostel_room_service.get_room(session, bed.room_id)
        if room.status == HostelRoomStatus.MAINTENANCE: _bad_request("Room is under maintenance")
        if room.occupancy >= room.capacity: _bad_request("Room is full")
        try:
            allocation = await self.repository.create(session, {**data, "status": HostelAllocationStatus.ACTIVE})
            bed.status = HostelBedStatus.OCCUPIED
            room.occupancy += 1
            room.status = HostelRoomStatus.FULL if room.occupancy == room.capacity else HostelRoomStatus.AVAILABLE
            await session.commit()
            await session.refresh(allocation)
            return allocation
        except Exception:
            await session.rollback()
            raise
    async def checkout(self, session: AsyncSession, allocation_id: UUID, checkout_date: date):
        allocation = await self.get(session, allocation_id)
        if allocation.status != HostelAllocationStatus.ACTIVE: _bad_request("Only active allocations can be checked out")
        if checkout_date < allocation.check_in_date: _bad_request("Checkout date cannot be before check-in date")
        bed = await hostel_bed_service.get_bed(session, allocation.bed_id)
        room = await hostel_room_service.get_room(session, bed.room_id)
        try:
            allocation.status, allocation.check_out_date = HostelAllocationStatus.CHECKED_OUT, checkout_date
            bed.status = HostelBedStatus.VACANT
            room.occupancy = max(0, room.occupancy - 1)
            if room.status != HostelRoomStatus.MAINTENANCE: room.status = HostelRoomStatus.AVAILABLE
            await session.commit()
            await session.refresh(allocation)
            return allocation
        except Exception:
            await session.rollback()
            raise
    async def transfer(self, session: AsyncSession, allocation_id: UUID, data: dict):
        allocation = await self.get(session, allocation_id)
        if allocation.status != HostelAllocationStatus.ACTIVE: _bad_request("Only active allocations can be transferred")
        if data["check_in_date"] < allocation.check_in_date: _bad_request("Transfer date cannot be before check-in date")
        new_bed = await hostel_bed_service.get_bed(session, data["bed_id"])
        if new_bed.id == allocation.bed_id: _bad_request("New bed must differ from the current bed")
        if new_bed.status != HostelBedStatus.VACANT: _bad_request("Bed is not vacant")
        new_room = await hostel_room_service.get_room(session, new_bed.room_id)
        if new_room.status == HostelRoomStatus.MAINTENANCE or new_room.occupancy >= new_room.capacity: _bad_request("New room is unavailable")
        old_bed = await hostel_bed_service.get_bed(session, allocation.bed_id)
        old_room = await hostel_room_service.get_room(session, old_bed.room_id)
        try:
            allocation.status, allocation.check_out_date = HostelAllocationStatus.TRANSFERRED, data["check_in_date"]
            old_bed.status, old_room.occupancy = HostelBedStatus.VACANT, max(0, old_room.occupancy - 1)
            if old_room.status != HostelRoomStatus.MAINTENANCE: old_room.status = HostelRoomStatus.AVAILABLE
            new_allocation = await self.repository.create(session, {"student_id": allocation.student_id, "bed_id": new_bed.id, "check_in_date": data["check_in_date"], "status": HostelAllocationStatus.ACTIVE})
            new_bed.status, new_room.occupancy = HostelBedStatus.OCCUPIED, new_room.occupancy + 1
            new_room.status = HostelRoomStatus.FULL if new_room.occupancy == new_room.capacity else HostelRoomStatus.AVAILABLE
            await session.commit()
            await session.refresh(new_allocation)
            return new_allocation
        except Exception:
            await session.rollback()
            raise
    async def get_allocation(self, session, item_id): return await self.get(session, item_id)
    async def get_allocations(self, session): return await self.list(session)
    async def get_student_allocation(self, session, student_id):
        if await session.get(Student, student_id) is None: _bad_request("Student must exist")
        allocation = await self.repository.get_student_allocation(session, student_id)
        if allocation is None: raise HTTPException(status_code=404, detail="Student hostel allocation not found")
        return allocation
    async def dashboard(self, session):
        total_blocks = await session.scalar(select(func.count(HostelBlock.id))) or 0
        total_rooms = await session.scalar(select(func.count(HostelRoom.id))) or 0
        total_beds = await session.scalar(select(func.count(HostelBed.id))) or 0
        occupied_beds = await session.scalar(select(func.count(HostelBed.id)).where(HostelBed.status == HostelBedStatus.OCCUPIED)) or 0
        active_allocations = await session.scalar(select(func.count(HostelAllocation.id)).where(HostelAllocation.status == HostelAllocationStatus.ACTIVE)) or 0
        return {"total_blocks": total_blocks, "total_rooms": total_rooms, "total_beds": total_beds, "occupied_beds": occupied_beds, "vacant_beds": total_beds - occupied_beds, "active_allocations": active_allocations}


hostel_block_service = HostelBlockService(hostel_block_repository, "Hostel block", ("block_name",), foreign_keys={"warden_id": User})
hostel_room_service = HostelRoomService(hostel_room_repository, "Hostel room", unique_constraints=(("block_id", "room_no"),), foreign_keys={"block_id": HostelBlock})
hostel_bed_service = HostelBedService(hostel_bed_repository, "Hostel bed", unique_constraints=(("room_id", "bed_no"),), foreign_keys={"room_id": HostelRoom})
hostel_allocation_service = HostelAllocationService(hostel_allocation_repository, "Hostel allocation")
