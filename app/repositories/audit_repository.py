from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_model import AuditLog, LoginHistory


class LoginHistoryRepository:
    async def create(self, session: AsyncSession, data: dict):
        item = LoginHistory(**data)
        session.add(item)
        await session.flush()
        await session.refresh(item)
        return item

    async def get_by_id(self, session: AsyncSession, item_id: UUID):
        return await session.get(LoginHistory, item_id)

    async def get_all(self, session: AsyncSession):
        return list((await session.execute(select(LoginHistory).order_by(LoginHistory.login_time.desc()))).scalars().all())

    async def update(self, session: AsyncSession, item: LoginHistory, data: dict):
        for field, value in data.items():
            setattr(item, field, value)
        await session.flush()
        await session.refresh(item)
        return item

    async def delete(self, session: AsyncSession, item: LoginHistory):
        await session.delete(item)
        await session.flush()

    async def get_by_user(self, session: AsyncSession, user_id: UUID):
        query = select(LoginHistory).where(LoginHistory.user_id == user_id).order_by(LoginHistory.login_time.desc())
        return list((await session.execute(query)).scalars().all())


class AuditLogRepository:
    async def create(self, session: AsyncSession, data: dict):
        item = AuditLog(**data)
        session.add(item)
        await session.flush()
        await session.refresh(item)
        return item

    async def get_by_id(self, session: AsyncSession, item_id: UUID):
        query = select(AuditLog).options(selectinload(AuditLog.user)).where(AuditLog.id == item_id)
        return (await session.execute(query)).scalar_one_or_none()

    async def get_all(self, session: AsyncSession, skip: int = 0, limit: int = 100):
        query = (
            select(AuditLog)
            .options(selectinload(AuditLog.user))
            .order_by(AuditLog.activity_time.desc())
            .offset(skip)
            .limit(limit)
        )
        return list((await session.execute(query)).scalars().all())

    async def get_recent(self, session: AsyncSession, limit: int = 20):
        query = (
            select(AuditLog)
            .options(selectinload(AuditLog.user))
            .order_by(AuditLog.activity_time.desc())
            .limit(limit)
        )
        return list((await session.execute(query)).scalars().all())

    async def delete(self, session: AsyncSession, item: AuditLog):
        await session.delete(item)
        await session.flush()

    async def get_by_user(self, session: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 100):
        query = (
            select(AuditLog)
            .options(selectinload(AuditLog.user))
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.activity_time.desc())
            .offset(skip)
            .limit(limit)
        )
        return list((await session.execute(query)).scalars().all())


login_history_repository = LoginHistoryRepository()
audit_log_repository = AuditLogRepository()

