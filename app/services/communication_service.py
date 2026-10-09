from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.communication_repository import announcement_repository, message_repository, notification_repository
from app.services.crud_service import CRUDService

AUDIENCES = {"ALL", "STUDENTS", "TEACHERS", "PARENTS", "ADMINS"}


class AnnouncementService(CRUDService):
    async def create(self, session, data):
        await self._validate(session, data)
        return await super().create(session, data)
    async def update(self, session, item_id, data):
        if "target_audience" in data and data["target_audience"] not in AUDIENCES: raise HTTPException(status_code=400, detail="Invalid target audience")
        return await super().update(session, item_id, data)
    async def _validate(self, session, data):
        if data["target_audience"] not in AUDIENCES: raise HTTPException(status_code=400, detail="Invalid target audience")
        if await session.get(User, data["created_by"]) is None: raise HTTPException(status_code=400, detail="Announcement creator must be a valid user")
    async def create_announcement(self, session, data): return await self.create(session, data)
    async def update_announcement(self, session, item_id, data): return await self.update(session, item_id, data)
    async def delete_announcement(self, session, item_id): return await self.delete(session, item_id)
    async def get_announcements(self, session): return await self.list(session)


class NotificationService(CRUDService):
    async def create(self, session, data):
        if await session.get(User, data["user_id"]) is None: raise HTTPException(status_code=400, detail="Notification user must be valid")
        return await super().create(session, data)
    async def mark_as_read(self, session, item_id): return await self.update(session, item_id, {"is_read": True})
    async def mark_all_as_read(self, session, user_id):
        from app.models.communication_model import Notification
        from sqlalchemy import update
        await session.execute(
            update(Notification).where(Notification.user_id == user_id, Notification.is_read == False).values(is_read=True)
        )
        await session.commit()
        return {"message": "All notifications marked as read"}
    async def get_notifications(self, session, user_id=None): return await self.repository.get_by_user(session, user_id) if user_id else await self.list(session)


class MessageService(CRUDService):
    async def create(self, session, data):
        await self._validate(session, data)
        return await super().create(session, data)
    async def update(self, session, item_id, data):
        if "message" in data and not data["message"].strip(): raise HTTPException(status_code=400, detail="Message text cannot be empty")
        return await super().update(session, item_id, data)
    async def _validate(self, session, data):
        if not (data.get("message") or "").strip(): raise HTTPException(status_code=400, detail="Message text cannot be empty")
        if not data.get("sender_id") or not data.get("receiver_id"):
            raise HTTPException(status_code=400, detail="Sender and receiver must be specified")
        if await session.get(User, data["sender_id"]) is None or await session.get(User, data["receiver_id"]) is None: raise HTTPException(status_code=400, detail="Sender and receiver must be valid users")
    async def send_message(self, session, data): return await self.create(session, data)
    async def mark_as_read(self, session, item_id): return await self.update(session, item_id, {"is_read": True})
    async def mark_all_as_read(self, session, user_id):
        from app.models.communication_model import Message
        from sqlalchemy import update
        await session.execute(
            update(Message).where(Message.receiver_id == user_id, Message.is_read == False).values(is_read=True)
        )
        await session.commit()
        return {"message": "All messages marked as read"}
    async def get_conversation(self, session, sender_id, receiver_id): return await self.repository.get_conversation(session, sender_id, receiver_id)
    async def get_user_messages(self, session, user_id):
        return await self.repository.get_sent_messages(session, user_id) + await self.repository.get_received_messages(session, user_id)


announcement_service = AnnouncementService(announcement_repository, "Announcement")
notification_service = NotificationService(notification_repository, "Notification")
message_service = MessageService(message_repository, "Message")
