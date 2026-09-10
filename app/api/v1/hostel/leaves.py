from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.hostel_operations_schema import HostelLeaveRequestCreate, HostelLeaveRequestResponse, HostelLeaveRequestUpdate
from app.services.hostel_operations_service import hostel_leave_request_service
from app.api.v1.auth.routes import get_current_user
from app.models.user import User

hostel_leave_router = APIRouter()

@hostel_leave_router.post("", response_model=HostelLeaveRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_leave_request(payload: HostelLeaveRequestCreate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await hostel_leave_request_service.create(session, payload.model_dump())

@hostel_leave_router.get("", response_model=list[HostelLeaveRequestResponse])
async def list_leave_requests(session: AsyncSession = Depends(get_db)):
    return await hostel_leave_request_service.list(session)

@hostel_leave_router.get("/{item_id}", response_model=HostelLeaveRequestResponse)
async def get_leave_request(item_id: UUID, session: AsyncSession = Depends(get_db)):
    return await hostel_leave_request_service.get(session, item_id)

@hostel_leave_router.put("/{item_id}", response_model=HostelLeaveRequestResponse)
async def update_leave_request(item_id: UUID, payload: HostelLeaveRequestUpdate, session: AsyncSession = Depends(get_db)):
    return await hostel_leave_request_service.update(session, item_id, payload.model_dump(exclude_unset=True))

@hostel_leave_router.delete("/{item_id}")
async def delete_leave_request(item_id: UUID, session: AsyncSession = Depends(get_db)):
    await hostel_leave_request_service.delete(session, item_id)
    return {"message": "Deleted successfully"}

@hostel_leave_router.patch("/{item_id}/approve", response_model=HostelLeaveRequestResponse)
async def approve_leave_request(item_id: UUID, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await hostel_leave_request_service.approve(session, item_id, {"approved_by": current_user.id})

@hostel_leave_router.patch("/{item_id}/reject", response_model=HostelLeaveRequestResponse)
async def reject_leave_request(item_id: UUID, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await hostel_leave_request_service.reject(session, item_id, {"approved_by": current_user.id})

@hostel_leave_router.get("/student/{student_id}", response_model=list[HostelLeaveRequestResponse])
async def student_leave_requests(student_id: UUID, session: AsyncSession = Depends(get_db)):
    return await hostel_leave_request_service.repository.get_by_field(session, "student_id", student_id)