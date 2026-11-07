from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hostel_model import (
    HostelAllocation,
    HostelAllocationStatus,
    HostelBed,
    HostelBedStatus,
    HostelBlock,
    HostelRoom,
)
from app.repositories.crud_repository import CRUDRepository


class HostelBlockRepository(CRUDRepository[HostelBlock]):
    async def get_by_id(self, session: AsyncSession, item_id: UUID): return await self.get(session, item_id)
    async def get_all(self, session: AsyncSession): return await self.list(session)
    async def get_block_rooms(self, session: AsyncSession, block_id: UUID):
        return list((await session.execute(select(HostelRoom).where(HostelRoom.block_id == block_id))).scalars().all())


class HostelRoomRepository(CRUDRepository[HostelRoom]):
    async def get_by_id(self, session: AsyncSession, item_id: UUID): return await self.get(session, item_id)
    async def get_all(self, session: AsyncSession): return await self.list(session)
    async def get_room_beds(self, session: AsyncSession, room_id: UUID):
        return list((await session.execute(select(HostelBed).where(HostelBed.room_id == room_id))).scalars().all())


class HostelBedRepository(CRUDRepository[HostelBed]):
    async def get_by_id(self, session: AsyncSession, item_id: UUID): return await self.get(session, item_id)
    async def get_all(self, session: AsyncSession): return await self.list(session)
    async def get_available_beds(self, session: AsyncSession):
        return list((await session.execute(select(HostelBed).where(HostelBed.status == HostelBedStatus.VACANT))).scalars().all())


class HostelAllocationRepository(CRUDRepository[HostelAllocation]):
    async def get_by_id(self, session: AsyncSession, item_id: UUID): return await self.get(session, item_id)
    async def get_all(self, session: AsyncSession): return await self.list(session)
    async def get_student_allocation(self, session: AsyncSession, student_id: UUID):
        return (await session.execute(select(HostelAllocation).where(HostelAllocation.student_id == student_id, HostelAllocation.status == HostelAllocationStatus.ACTIVE))).scalar_one_or_none()
    async def get_bed_allocation(self, session: AsyncSession, bed_id: UUID):
        return (await session.execute(select(HostelAllocation).where(HostelAllocation.bed_id == bed_id, HostelAllocation.status == HostelAllocationStatus.ACTIVE))).scalar_one_or_none()


hostel_block_repository = HostelBlockRepository(HostelBlock)
hostel_room_repository = HostelRoomRepository(HostelRoom)
hostel_bed_repository = HostelBedRepository(HostelBed)
hostel_allocation_repository = HostelAllocationRepository(HostelAllocation)
