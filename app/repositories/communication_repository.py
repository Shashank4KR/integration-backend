from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.communication_model import Announcement, Message, Notification
from app.repositories.crud_repository import CRUDRepository


class AnnouncementRepository(CRUDRepository[Announcement]):
    async def get_by_id(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)
    async def get_all(self, session: AsyncSession):
        return await self.list(session)


class NotificationRepository(CRUDRepository[Notification]):
    async def get_by_id(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)
    async def get_all(self, session: AsyncSession):
        return await self.list(session)
    async def get_by_user(self, session: AsyncSession, user_id: UUID):
        return list((await session.execute(select(Notification).where(Notification.user_id == user_id))).scalars().all())


class MessageRepository(CRUDRepository[Message]):
    async def get_by_id(self, session: AsyncSession, item_id: UUID):
        return await self.get(session, item_id)
    async def get_all(self, session: AsyncSession):
        return await self.list(session)
    async def get_conversation(self, session: AsyncSession, sender_id: UUID, receiver_id: UUID):
        query = select(Message).where(or_((Message.sender_id == sender_id) & (Message.receiver_id == receiver_id), (Message.sender_id == receiver_id) & (Message.receiver_id == sender_id))).order_by(Message.sent_on)
        return list((await session.execute(query)).scalars().all())
    async def get_sent_messages(self, session: AsyncSession, user_id: UUID):
        return list((await session.execute(select(Message).where(Message.sender_id == user_id))).scalars().all())
    async def get_received_messages(self, session: AsyncSession, user_id: UUID):
        return list((await session.execute(select(Message).where(Message.receiver_id == user_id))).scalars().all())


announcement_repository = AnnouncementRepository(Announcement)
notification_repository = NotificationRepository(Notification)
message_repository = MessageRepository(Message)
