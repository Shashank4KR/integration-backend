from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.hostel_operations_schema import HostelNoticeCreate, HostelNoticeResponse, HostelNoticeUpdate
from app.services.hostel_operations_service import hostel_notice_service
from app.api.v1.auth.routes import get_current_user
from app.models.user import User

hostel_notice_router = APIRouter()

def _ensure_admin_or_warden(current_user: User) -> None:
    role_name = (current_user.role.role_name if current_user.role else "").upper()
    if role_name not in ("ADMIN", "WARDEN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or warden users can perform this action",
        )

@hostel_notice_router.post("", response_model=HostelNoticeResponse, status_code=status.HTTP_201_CREATED)
async def create_notice(payload: HostelNoticeCreate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    return await hostel_notice_service.create(session, payload.model_dump())

@hostel_notice_router.get("", response_model=list[HostelNoticeResponse])
async def list_notices(session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await hostel_notice_service.list(session)

@hostel_notice_router.get("/published", response_model=list[HostelNoticeResponse])
async def list_published_notices(session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await hostel_notice_service.list_published(session)

@hostel_notice_router.get("/{item_id}", response_model=HostelNoticeResponse)
async def get_notice(item_id: UUID, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await hostel_notice_service.get(session, item_id)

@hostel_notice_router.put("/{item_id}", response_model=HostelNoticeResponse)
async def update_notice(
    item_id: UUID,
    payload: HostelNoticeUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_warden(current_user)
    return await hostel_notice_service.update(session, item_id, payload.model_dump(exclude_unset=True))

@hostel_notice_router.delete("/{item_id}")
async def delete_notice(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_warden(current_user)
    await hostel_notice_service.delete(session, item_id)
    return {"message": "Deleted successfully"}

@hostel_notice_router.patch("/{item_id}/publish", response_model=HostelNoticeResponse)
async def publish_notice(item_id: UUID, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    return await hostel_notice_service.publish(session, item_id)