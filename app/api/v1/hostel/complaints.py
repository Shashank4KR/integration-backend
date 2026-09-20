from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.hostel_operations_schema import HostelComplaintCreate, HostelComplaintResponse, HostelComplaintUpdate, HostelComplaintSummaryResponse
from app.services.hostel_operations_service import hostel_complaint_service
from app.api.v1.auth.routes import get_current_user
from app.models.user import User
from app.models.student_model import Student

hostel_complaint_router = APIRouter()

def _ensure_admin_or_warden(current_user: User) -> None:
    role_name = (current_user.role.role_name if current_user.role else "").upper()
    if role_name not in ("ADMIN", "WARDEN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or warden users can perform this action",
        )

@hostel_complaint_router.post("", response_model=HostelComplaintResponse, status_code=status.HTTP_201_CREATED)
async def create_complaint(payload: HostelComplaintCreate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await hostel_complaint_service.create(session, payload.model_dump())

@hostel_complaint_router.get("", response_model=list[HostelComplaintResponse])
async def list_complaints(session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await hostel_complaint_service.list(session)

@hostel_complaint_router.get("/{item_id}", response_model=HostelComplaintResponse)
async def get_complaint(item_id: UUID, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await hostel_complaint_service.get(session, item_id)

@hostel_complaint_router.put("/{item_id}", response_model=HostelComplaintResponse)
async def update_complaint(
    item_id: UUID,
    payload: HostelComplaintUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    complaint = await hostel_complaint_service.get(session, item_id)
    role_name = (current_user.role.role_name if current_user.role else "").upper()
    if role_name not in ("ADMIN", "WARDEN"):
        student_res = await session.execute(select(Student).where(Student.user_id == current_user.id))
        student = student_res.scalar_one_or_none()
        if not student or student.id != complaint.student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this complaint",
            )
    return await hostel_complaint_service.update(session, item_id, payload.model_dump(exclude_unset=True))

@hostel_complaint_router.delete("/{item_id}")
async def delete_complaint(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_warden(current_user)
    await hostel_complaint_service.delete(session, item_id)
    return {"message": "Deleted successfully"}

@hostel_complaint_router.patch("/{item_id}/resolve", response_model=HostelComplaintResponse)
async def resolve_complaint(item_id: UUID, payload: HostelComplaintUpdate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    return await hostel_complaint_service.resolve(session, item_id, payload.model_dump(exclude_unset=True))

@hostel_complaint_router.get("/summary", response_model=HostelComplaintSummaryResponse)
async def complaint_summary(session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = await hostel_complaint_service.list(session)
    return HostelComplaintSummaryResponse(
        total_open=sum(1 for i in items if i.resolution_status == "OPEN"),
        total_in_progress=sum(1 for i in items if i.resolution_status == "IN_PROGRESS"),
        total_resolved=sum(1 for i in items if i.resolution_status == "RESOLVED"),
        total_closed=sum(1 for i in items if i.resolution_status == "CLOSED"),
    )