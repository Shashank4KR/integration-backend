from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_model import AuditLog, LoginHistory
from app.models.user import User
from app.repositories.audit_repository import audit_log_repository, login_history_repository


class LoginHistoryService:
    async def create_login_record(self, session: AsyncSession, data: dict, commit: bool = True):
        if await session.get(User, data["user_id"]) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must exist")
        if data.get("login_time") is None:
            data["login_time"] = datetime.now(timezone.utc)
        item = await login_history_repository.create(session, data)
        if commit:
            await session.commit()
        return item

    async def update_logout_record(self, session: AsyncSession, record_id: UUID, commit: bool = True):
        item = await self.get_history(session, record_id)
        if item.logout_time is None:
            item = await login_history_repository.update(session, item, {"logout_time": datetime.now(timezone.utc)})
            if commit:
                await session.commit()
        return item

    async def get_user_history(self, session: AsyncSession, user_id: UUID):
        await _ensure_user(session, user_id)
        return await login_history_repository.get_by_user(session, user_id)

    async def get_history_all(self, session: AsyncSession):
        return await login_history_repository.get_all(session)

    async def get_history(self, session: AsyncSession, record_id: UUID):
        item = await login_history_repository.get_by_id(session, record_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Login history record not found")
        return item


class AuditLogService:
    async def create_log(self, session: AsyncSession, data: dict, commit: bool = True):
        await _ensure_user(session, data["user_id"])
        if not data["activity"].strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Activity cannot be empty")
        if data.get("activity_time") is None:
            data["activity_time"] = datetime.now(timezone.utc)
        item = await audit_log_repository.create(session, data)
        if commit:
            await session.commit()
        return item

    async def get_logs(self, session: AsyncSession, skip: int = 0, limit: int = 100):
        return await audit_log_repository.get_all(session, skip=skip, limit=limit)

    async def get_log(self, session: AsyncSession, log_id: UUID):
        item = await audit_log_repository.get_by_id(session, log_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit log not found")
        return item

    async def get_user_logs(self, session: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 100):
        await _ensure_user(session, user_id)
        return await audit_log_repository.get_by_user(session, user_id, skip=skip, limit=limit)

    async def security_dashboard(self, session: AsyncSession) -> dict:
        today = datetime.now(timezone.utc).date()
        logins = await session.scalar(select(func.count(LoginHistory.id)).where(func.date(LoginHistory.login_time) == today))
        active = await session.scalar(select(func.count(LoginHistory.id)).where(LoginHistory.logout_time.is_(None)))
        logs = await session.scalar(select(func.count(AuditLog.id)).where(func.date(AuditLog.activity_time) == today))
        return {"total_logins_today": logins or 0, "active_sessions": active or 0, "audit_logs_today": logs or 0}

    async def recent_activities(self, session: AsyncSession):
        return await audit_log_repository.get_recent(session, limit=20)

    async def user_activity_timeline(self, session: AsyncSession, user_id: UUID):
        logs = await self.get_user_logs(session, user_id)
        history = await login_history_service.get_user_history(session, user_id)
        events = ([{"type": "audit", "activity": log.activity, "activity_time": log.activity_time, "details": log.details, "id": log.id} for log in logs]
                  + [{"type": "login", "activity": "User Login", "activity_time": row.login_time, "details": row.device or row.ip_address, "id": row.id} for row in history]
                  + [{"type": "logout", "activity": "User Logout", "activity_time": row.logout_time, "details": None, "id": row.id} for row in history if row.logout_time])
        return sorted(events, key=lambda event: event["activity_time"], reverse=True)

    async def login_statistics(self, session: AsyncSession) -> dict:
        now = datetime.now(timezone.utc)
        async def count_since(since):
            return (await session.scalar(select(func.count(LoginHistory.id)).where(LoginHistory.login_time >= since))) or 0
        week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        return {
            "today": await count_since(now.replace(hour=0, minute=0, second=0, microsecond=0)),
            "this_week": await count_since(week_start),
            "this_month": await count_since(now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)),
        }


async def _ensure_user(session: AsyncSession, user_id: UUID) -> None:
    if await session.get(User, user_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must exist")


login_history_service = LoginHistoryService()
audit_log_service = AuditLogService()
