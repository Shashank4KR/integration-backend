from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.hostel_operations_schema import HostelSettingCreate, HostelSettingResponse, HostelSettingUpdate
from app.services.hostel_operations_service import hostel_setting_service
from app.api.v1.auth.routes import get_current_user
from app.models.user import User

hostel_setting_router = APIRouter()

def _ensure_admin_or_warden(current_user: User) -> None:
    role_name = (current_user.role.role_name if current_user.role else "").upper()
    if role_name not in ("ADMIN", "WARDEN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or warden users can perform this action",
        )

@hostel_setting_router.post("", response_model=HostelSettingResponse, status_code=status.HTTP_201_CREATED)
async def create_setting(payload: HostelSettingCreate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    return await hostel_setting_service.create(session, payload.model_dump())

@hostel_setting_router.get("", response_model=list[HostelSettingResponse])
async def list_settings(session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await hostel_setting_service.list(session)

@hostel_setting_router.get("/{item_id}", response_model=HostelSettingResponse)
async def get_setting(item_id: UUID, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await hostel_setting_service.get(session, item_id)

@hostel_setting_router.put("/{item_id}", response_model=HostelSettingResponse)
async def update_setting(
    item_id: UUID,
    payload: HostelSettingUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_warden(current_user)
    return await hostel_setting_service.update(session, item_id, payload.model_dump(exclude_unset=True))

@hostel_setting_router.delete("/{item_id}")
async def delete_setting(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_warden(current_user)
    await hostel_setting_service.delete(session, item_id)
    return {"message": "Deleted successfully"}