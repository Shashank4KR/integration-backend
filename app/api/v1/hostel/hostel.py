from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.models.hostel_model import HostelAllocation, HostelAllocationStatus, HostelBed, HostelBedStatus, HostelBlock, HostelRoom, HostelRoomStatus
from app.models.user import User
from app.schemas.hostel_schema import HostelAllocationCreate, HostelAllocationResponse, HostelBedCreate, HostelBedResponse, HostelBedUpdate, HostelBlockCreate, HostelBlockResponse, HostelBlockUpdate, HostelRoomCreate, HostelRoomResponse, HostelRoomUpdate, HostelTransferRequest
from app.services.audit_service import audit_log_service
from app.services.communication_service import notification_service
from app.services.hostel_service import hostel_allocation_service, hostel_bed_service, hostel_block_service, hostel_room_service

async def _audit(session, user_id, activity, details):
    try:
        await audit_log_service.create_log(session, {"user_id": user_id, "activity": activity, "details": details}, commit=False)
    except Exception:
        pass

async def _notify(session, user_id, title, message):
    try:
        await notification_service.create(session, {"user_id": user_id, "title": title, "message": message}, commit=False)
    except Exception:
        pass

def _ensure_admin_or_warden(current_user: User) -> None:
    if current_user.role.role_name not in ("ADMIN", "WARDEN"):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or warden users can perform this action",
        )


block_router = APIRouter()
@block_router.post("", response_model=HostelBlockResponse, status_code=status.HTTP_201_CREATED)
async def create_block(payload: HostelBlockCreate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    result = await hostel_block_service.create_block(session, payload.model_dump())
    await _audit(session, current_user.id, "Create Hostel Block", f"Created block {payload.block_name}")
    return result
@block_router.get("", response_model=list[HostelBlockResponse])
async def get_blocks(session: AsyncSession = Depends(get_db)):
    return await hostel_block_service.get_blocks(session)
@block_router.get("/{item_id}", response_model=HostelBlockResponse)
async def get_block(item_id: UUID, session: AsyncSession = Depends(get_db)):
    return await hostel_block_service.get_block(session, item_id)
@block_router.put("/{item_id}", response_model=HostelBlockResponse)
async def update_block(item_id: UUID, payload: HostelBlockUpdate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    result = await hostel_block_service.update_block(session, item_id, payload.model_dump(exclude_unset=True))
    await _audit(session, current_user.id, "Update Hostel Block", f"Updated block {item_id}")
    return result
@block_router.delete("/{item_id}")
async def delete_block(item_id: UUID, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    await hostel_block_service.delete_block(session, item_id)
    await _audit(session, current_user.id, "Delete Hostel Block", f"Deleted block {item_id}")
    return {"message": "Deleted successfully"}

room_router = APIRouter()
@room_router.post("", response_model=HostelRoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(payload: HostelRoomCreate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    result = await hostel_room_service.create_room(session, payload.model_dump())
    await _audit(session, current_user.id, "Create Hostel Room", f"Created room {payload.room_no}")
    return result
@room_router.get("", response_model=list[HostelRoomResponse])
async def get_rooms(session: AsyncSession = Depends(get_db)):
    return await hostel_room_service.get_rooms(session)
@room_router.get("/{item_id}", response_model=HostelRoomResponse)
async def get_room(item_id: UUID, session: AsyncSession = Depends(get_db)):
    return await hostel_room_service.get_room(session, item_id)
@room_router.put("/{item_id}", response_model=HostelRoomResponse)
async def update_room(item_id: UUID, payload: HostelRoomUpdate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    result = await hostel_room_service.update_room(session, item_id, payload.model_dump(exclude_unset=True))
    await _audit(session, current_user.id, "Update Hostel Room", f"Updated room {item_id}")
    return result
@room_router.delete("/{item_id}")
async def delete_room(item_id: UUID, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    await hostel_room_service.delete_room(session, item_id)
    await _audit(session, current_user.id, "Delete Hostel Room", f"Deleted room {item_id}")
    return {"message": "Deleted successfully"}

bed_router = APIRouter()
@bed_router.post("", response_model=HostelBedResponse, status_code=status.HTTP_201_CREATED)
async def create_bed(payload: HostelBedCreate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    result = await hostel_bed_service.create_bed(session, payload.model_dump())
    await _audit(session, current_user.id, "Create Hostel Bed", f"Created bed {payload.bed_no}")
    return result
@bed_router.get("/available", response_model=list[HostelBedResponse])
async def get_available_beds(session: AsyncSession = Depends(get_db)):
    return await hostel_bed_service.get_available_beds(session)
@bed_router.get("", response_model=list[HostelBedResponse])
async def get_beds(session: AsyncSession = Depends(get_db)):
    return await hostel_bed_service.get_beds(session)
@bed_router.get("/{item_id}", response_model=HostelBedResponse)
async def get_bed(item_id: UUID, session: AsyncSession = Depends(get_db)):
    return await hostel_bed_service.get_bed(session, item_id)
@bed_router.put("/{item_id}", response_model=HostelBedResponse)
async def update_bed(item_id: UUID, payload: HostelBedUpdate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    result = await hostel_bed_service.update_bed(session, item_id, payload.model_dump(exclude_unset=True))
    await _audit(session, current_user.id, "Update Hostel Bed", f"Updated bed {item_id}")
    return result
@bed_router.delete("/{item_id}")
async def delete_bed(item_id: UUID, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    await hostel_bed_service.delete_bed(session, item_id)
    await _audit(session, current_user.id, "Delete Hostel Bed", f"Deleted bed {item_id}")
    return {"message": "Deleted successfully"}

allocation_router = APIRouter()
@allocation_router.post("/allocate", response_model=HostelAllocationResponse, status_code=status.HTTP_201_CREATED)
async def allocate_student(payload: HostelAllocationCreate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    result = await hostel_allocation_service.allocate(session, payload.model_dump())
    await _audit(session, current_user.id, "Allocate Student to Hostel", f"Allocated student {payload.student_id} to bed {payload.bed_id}")
    await _notify(session, payload.student_id, "Hostel Allocation", f"You have been allocated to a hostel bed.")
    return result
@allocation_router.post("", response_model=HostelAllocationResponse, status_code=status.HTTP_201_CREATED)
async def create_allocation(payload: HostelAllocationCreate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    return await allocate_student(payload, session, current_user)
@allocation_router.get("", response_model=list[HostelAllocationResponse])
async def get_allocations(session: AsyncSession = Depends(get_db)):
    return await hostel_allocation_service.get_allocations(session)
@allocation_router.get("/{item_id}", response_model=HostelAllocationResponse)
async def get_allocation(item_id: UUID, session: AsyncSession = Depends(get_db)):
    return await hostel_allocation_service.get_allocation(session, item_id)
@allocation_router.post("/{allocation_id}/checkout", response_model=HostelAllocationResponse)
async def checkout_student(allocation_id: UUID, checkout_date: date, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    result = await hostel_allocation_service.checkout(session, allocation_id, checkout_date)
    await _audit(session, current_user.id, "Checkout Student", f"Checked out student from allocation {allocation_id}")
    return result
@allocation_router.post("/{allocation_id}/transfer", response_model=HostelAllocationResponse)
async def transfer_student(allocation_id: UUID, payload: HostelTransferRequest, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    result = await hostel_allocation_service.transfer(session, allocation_id, payload.model_dump())
    await _audit(session, current_user.id, "Transfer Student", f"Transferred student from allocation {allocation_id}")
    return result

student_hostel_router = APIRouter()
@student_hostel_router.get("/{student_id}/hostel", response_model=HostelAllocationResponse)
async def get_student_hostel(student_id: UUID, session: AsyncSession = Depends(get_db)):
    return await hostel_allocation_service.get_student_allocation(session, student_id)

hostel_router = APIRouter()
@hostel_router.get("/dashboard")
async def hostel_dashboard(session: AsyncSession = Depends(get_db)):
    return await hostel_allocation_service.dashboard(session)

@hostel_router.get("/dashboard/stats")
async def hostel_dashboard_stats(session: AsyncSession = Depends(get_db)):
    await hostel_bed_service.ensure_room_beds(session)
    total_blocks = await session.scalar(select(func.count(HostelBlock.id))) or 0
    total_rooms = await session.scalar(select(func.count(HostelRoom.id))) or 0
    total_beds = await session.scalar(select(func.count(HostelBed.id))) or 0
    occupied_beds = await session.scalar(select(func.count(HostelBed.id)).where(HostelBed.status == HostelBedStatus.OCCUPIED)) or 0
    available_beds = total_beds - occupied_beds
    active_allocations = await session.scalar(select(func.count(HostelAllocation.id)).where(HostelAllocation.status == HostelAllocationStatus.ACTIVE)) or 0
    occupancy_pct = round((occupied_beds / total_beds * 100), 2) if total_beds > 0 else 0
    return {
        "total_blocks": total_blocks,
        "total_rooms": total_rooms,
        "total_beds": total_beds,
        "occupied_beds": occupied_beds,
        "available_beds": available_beds,
        "active_allocations": active_allocations,
        "occupancy_percentage": occupancy_pct,
    }
