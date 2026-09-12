from uuid import UUID

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.leave_schema import (
    LeaveApprovalRequest,
    LeaveRequestCreate,
    LeaveRequestResponse,
    LeaveRequestUpdate,
    LeaveSummaryResponse,
    LeaveTypeCreate,
    LeaveTypeResponse,
    LeaveTypeUpdate,
)
from app.services.leave_service import leave_request_service, leave_type_service

leave_type_router = APIRouter()
leave_request_router = APIRouter()
user_leave_router = APIRouter()


def _ensure_admin(current_user: User) -> None:
    if current_user.role.role_name != "ADMIN":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can perform this action",
        )


def _ensure_admin_or_teacher(current_user: User) -> None:
    if current_user.role.role_name not in ("ADMIN", "TEACHER"):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or teacher users can perform this action",
        )


@leave_type_router.post("", response_model=LeaveTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_leave_type(
    payload: LeaveTypeCreate, session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    return await leave_type_service.create_leave_type(session, payload.model_dump())


@leave_type_router.get("", response_model=list[LeaveTypeResponse])
async def get_leave_types(session: AsyncSession = Depends(get_db)):
    return await leave_type_service.get_leave_types(session)


@leave_type_router.get("/{leave_type_id}", response_model=LeaveTypeResponse)
async def get_leave_type(leave_type_id: UUID, session: AsyncSession = Depends(get_db)):
    return await leave_type_service.get_leave_type(session, leave_type_id)


@leave_type_router.put("/{leave_type_id}", response_model=LeaveTypeResponse)
async def update_leave_type(
    leave_type_id: UUID,
    payload: LeaveTypeUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    return await leave_type_service.update_leave_type(
        session, leave_type_id, payload.model_dump(exclude_unset=True)
    )


@leave_type_router.delete("/{leave_type_id}", status_code=status.HTTP_200_OK)
async def delete_leave_type(
    leave_type_id: UUID, session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    await leave_type_service.delete_leave_type(session, leave_type_id)
    return {"message": "Deleted successfully"}


@leave_request_router.post(
    "", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED
)
async def apply_leave(
    payload: LeaveRequestCreate, session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await leave_request_service.apply_leave(session, payload.model_dump())


@leave_request_router.get("", response_model=list[LeaveRequestResponse])
async def get_leaves(session: AsyncSession = Depends(get_db)):
    return await leave_request_service.get_leaves(session)


@leave_request_router.get("/pending", response_model=list[LeaveRequestResponse])
async def get_pending_leaves(session: AsyncSession = Depends(get_db)):
    return await leave_request_service.get_pending(session)


@leave_request_router.get("/summary", response_model=LeaveSummaryResponse)
async def get_leave_summary(session: AsyncSession = Depends(get_db)):
    return await leave_request_service.get_summary(session)


@leave_request_router.patch("/{leave_id}/approve", response_model=LeaveRequestResponse)
async def approve_leave(
    leave_id: UUID,
    payload: LeaveApprovalRequest = Body(default=LeaveApprovalRequest()),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_teacher(current_user)
    return await leave_request_service.approve_leave(session, leave_id, current_user)


@leave_request_router.patch("/{leave_id}/reject", response_model=LeaveRequestResponse)
async def reject_leave(
    leave_id: UUID,
    payload: LeaveApprovalRequest = Body(default=LeaveApprovalRequest()),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_teacher(current_user)
    return await leave_request_service.reject_leave(session, leave_id, current_user)


@leave_request_router.patch("/{leave_id}/cancel", response_model=LeaveRequestResponse)
async def cancel_leave(leave_id: UUID, session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await leave_request_service.cancel_leave(session, leave_id)


@leave_request_router.get("/{leave_id}", response_model=LeaveRequestResponse)
async def get_leave(leave_id: UUID, session: AsyncSession = Depends(get_db)):
    return await leave_request_service.get_leave(session, leave_id)


@leave_request_router.put("/{leave_id}", response_model=LeaveRequestResponse)
async def update_leave(
    leave_id: UUID,
    payload: LeaveRequestUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_teacher(current_user)
    return await leave_request_service.update_leave(
        session, leave_id, payload.model_dump(exclude_unset=True)
    )


@leave_request_router.delete("/{leave_id}", status_code=status.HTTP_200_OK)
async def delete_leave(
    leave_id: UUID, session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_teacher(current_user)
    await leave_request_service.delete_leave(session, leave_id)
    return {"message": "Deleted successfully"}


@user_leave_router.get("/{user_id}/leave-requests", response_model=list[LeaveRequestResponse])
async def get_user_leave_requests(
    user_id: UUID, session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.role_name not in ("ADMIN", "TEACHER") and str(current_user.id) != str(user_id):
        _ensure_admin_or_teacher(current_user)
    return await leave_request_service.get_user_leaves(session, user_id)
