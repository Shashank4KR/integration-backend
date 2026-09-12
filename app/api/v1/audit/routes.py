from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.audit_schema import AuditLogResponse, LoginHistoryResponse
from app.services.audit_service import audit_log_service, login_history_service

login_history_router = APIRouter()
audit_log_router = APIRouter()
audit_router = APIRouter()
user_audit_router = APIRouter()


@login_history_router.get("", response_model=list[LoginHistoryResponse])
async def get_login_history(session: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await login_history_service.get_history_all(session)


@login_history_router.get("/{record_id}", response_model=LoginHistoryResponse)
async def get_login_history_record(record_id: UUID, session: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await login_history_service.get_history(session, record_id)


@audit_log_router.get("", response_model=list[AuditLogResponse])
async def get_audit_logs(session: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await audit_log_service.get_logs(session)


@audit_log_router.get("/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(log_id: UUID, session: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await audit_log_service.get_log(session, log_id)


@audit_router.get("/security-dashboard")
async def security_dashboard(session: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await audit_log_service.security_dashboard(session)


@audit_router.get("/recent-activities", response_model=list[AuditLogResponse])
async def recent_activities(session: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await audit_log_service.recent_activities(session)


@audit_router.get("/login-statistics")
async def login_statistics(session: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await audit_log_service.login_statistics(session)


@user_audit_router.get("/{user_id}/login-history", response_model=list[LoginHistoryResponse])
async def user_login_history(user_id: UUID, session: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await login_history_service.get_user_history(session, user_id)


@user_audit_router.get("/{user_id}/audit-logs", response_model=list[AuditLogResponse])
async def user_audit_logs(user_id: UUID, session: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await audit_log_service.get_user_logs(session, user_id)


@user_audit_router.get("/{user_id}/activity-timeline")
async def user_activity_timeline(user_id: UUID, session: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await audit_log_service.user_activity_timeline(session, user_id)
