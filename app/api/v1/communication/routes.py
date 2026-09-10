from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.models.communication_model import Announcement, Message, Notification
from app.models.user import User
from app.models.role import Role
from app.schemas.communication_schema import AnnouncementCreate, AnnouncementResponse, AnnouncementUpdate, MessageCreate, MessageResponse, NotificationCreate, NotificationResponse, NotificationUpdate
from app.services.communication_service import announcement_service, message_service, notification_service

announcement_router = APIRouter()
notification_router = APIRouter()
message_router = APIRouter()
user_communication_router = APIRouter()
communication_router = APIRouter()


def _ensure_admin(current_user: User) -> None:
    if current_user.role.role_name != "ADMIN":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can perform this action",
        )


def _audiences_for_role(current_user: User) -> tuple[str, ...]:
    role_name = current_user.role.role_name.upper() if current_user.role else ""
    role_audience = {
        "ADMIN": "ADMINS",
        "STUDENT": "STUDENTS",
        "PARENT": "PARENTS",
        "TEACHER": "TEACHERS",
        "FACULTY": "TEACHERS",
    }.get(role_name)
    return ("ALL", role_audience) if role_audience else ("ALL",)


@communication_router.get("/statistics")
async def get_communication_statistics(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    total_messages = await session.scalar(select(func.count(Message.id)))
    unread_messages = await session.scalar(select(func.count(Message.id)).where(Message.is_read.is_(False)))
    total_announcements = await session.scalar(select(func.count(Announcement.id)))
    total_notifications = await session.scalar(select(func.count(Notification.id)))
    unread_notifications = await session.scalar(select(func.count(Notification.id)).where(Notification.is_read.is_(False)))
    total_communications = (total_messages or 0) + (total_announcements or 0) + (total_notifications or 0)

    return {
        "total_communications": total_communications,
        "total_messages": total_messages or 0,
        "unread_messages": unread_messages or 0,
        "total_announcements": total_announcements or 0,
        "total_notifications": total_notifications or 0,
        "unread_notifications": unread_notifications or 0,
        "delivered": total_communications,
        "failed": 0,
        "delivery_rate": 100 if total_communications else 0,
        "channels": [
            {"label": "Messages", "value": total_messages or 0},
            {"label": "Announcements", "value": total_announcements or 0},
            {"label": "Notifications", "value": total_notifications or 0},
        ],
        "audiences": [],
        "delivery": [
            {"label": "Delivered", "value": total_communications},
            {"label": "Failed", "value": 0},
        ],
        "types": [
            {"type": "Messages", "messages": total_messages or 0},
            {"type": "Announcements", "messages": total_announcements or 0},
            {"type": "Notifications", "messages": total_notifications or 0},
        ],
    }


@announcement_router.post("", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
async def create_announcement(payload: AnnouncementCreate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    return await announcement_service.create_announcement(session, payload.model_dump())
@announcement_router.get("", response_model=list[AnnouncementResponse])
async def get_announcements(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.role_name == "ADMIN":
        return await announcement_service.get_announcements(session)
    result = await session.execute(
        select(Announcement).where(Announcement.target_audience.in_(_audiences_for_role(current_user)))
    )
    return result.scalars().all()
@announcement_router.get("/{item_id}", response_model=AnnouncementResponse)
async def get_announcement(item_id: UUID, session: AsyncSession = Depends(get_db)): return await announcement_service.get(session, item_id)
@announcement_router.put("/{item_id}", response_model=AnnouncementResponse)
async def update_announcement(item_id: UUID, payload: AnnouncementUpdate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    return await announcement_service.update_announcement(session, item_id, payload.model_dump(exclude_unset=True))
@announcement_router.delete("/{item_id}")
async def delete_announcement(item_id: UUID, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    await announcement_service.delete_announcement(session, item_id)
    return {"message": "Deleted successfully"}

notification_router = APIRouter()
@notification_router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(
    payload: NotificationCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    _ensure_admin(current_user)
    if payload.audience:
        from app.models.role import Role
        from app.models.user import User
        from sqlalchemy import select
        from fastapi import HTTPException

        aud = payload.audience.upper()
        if aud == "ALL":
            result = await session.execute(select(User))
            users = result.scalars().all()
        else:
            aud_map = {
                "STUDENTS": ["STUDENT"],
                "PARENTS": ["PARENT"],
                "TEACHERS": ["TEACHER"],
                "STAFF": ["TEACHER", "ACCOUNTANT", "LIBRARIAN", "WARDEN"]
            }
            role_names = aud_map.get(aud, [])
            if role_names:
                role_result = await session.execute(select(Role).where(Role.role_name.in_(role_names)))
                role_ids = [r.id for r in role_result.scalars().all()]
                if role_ids:
                    user_result = await session.execute(select(User).where(User.role_id.in_(role_ids)))
                    users = user_result.scalars().all()
                else:
                    users = []
            else:
                users = []

        if not users:
            raise HTTPException(status_code=400, detail="No users found in targeted audience")

        first_notif = None
        for u in users:
            notif_data = payload.model_dump(exclude_none=True)
            notif_data["user_id"] = u.id
            notif_data.pop("audience", None)
            notif = await notification_service.create(session, notif_data)
            if first_notif is None:
                first_notif = notif
        return first_notif
    
    if not payload.user_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="user_id is required when audience is not specified")

    return await notification_service.create(session, payload.model_dump(exclude_none=True))
@notification_router.get("", response_model=list[NotificationResponse])
async def get_notifications(
    scope: str = Query("me", description="Scope of notifications: 'me' for user inbox, 'all' for admin system view"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if scope == "all" and current_user.role and current_user.role.role_name == "ADMIN":
        return await notification_service.list(session)
    return await notification_service.get_notifications(session, current_user.id)
@notification_router.get("/{item_id}", response_model=NotificationResponse)
async def get_notification(item_id: UUID, session: AsyncSession = Depends(get_db)): return await notification_service.get(session, item_id)
@notification_router.put("/{item_id}", response_model=NotificationResponse)
async def update_notification(item_id: UUID, payload: NotificationUpdate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    return await notification_service.update(session, item_id, payload.model_dump(exclude_unset=True))
@notification_router.delete("/{item_id}")
async def delete_notification(item_id: UUID, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    await notification_service.delete(session, item_id)
    return {"message": "Deleted successfully"}
@notification_router.patch("/{item_id}/read", response_model=NotificationResponse)
async def mark_notification_read(item_id: UUID, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await notification_service.mark_as_read(session, item_id)

@notification_router.post("/read-all")
@notification_router.patch("/read-all")
async def mark_all_notifications_read(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await notification_service.mark_all_as_read(session, current_user.id)

@communication_router.get("/recipients")
async def get_recipients(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    users_result = await session.execute(
        select(User).join(Role, User.role_id == Role.id, isouter=True)
    )
    users = users_result.scalars().all()

    recipients = []
    for u in users:
        role_name = (u.role.role_name if u.role else "User").capitalize()
        display_name = f"{u.username} ({role_name})"
        recipients.append({
            "id": str(u.id),
            "username": u.username,
            "email": u.email,
            "role": role_name,
            "display_name": display_name,
        })
    return recipients


message_router = APIRouter()
@message_router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(payload: MessageCreate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    msg_text = (payload.message or payload.content or "").strip()
    if not msg_text:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Message content cannot be empty")

    sender_id = payload.sender_id or current_user.id

    target_val = (payload.recipient_id or payload.recipient or "").strip()
    
    # Strip any role suffix like "(Student)", "(Teacher)", "(Librarian)"
    clean_target = target_val.split("(")[0].strip() if "(" in target_val else target_val

    target_users: list[User] = []

    # 1. Try direct UUID
    if payload.receiver_id:
        u = await session.get(User, payload.receiver_id)
        if u:
            target_users.append(u)
    elif clean_target:
        try:
            target_uuid = UUID(clean_target)
            u = await session.get(User, target_uuid)
            if u:
                target_users.append(u)
        except ValueError:
            pass

    # 2. Try match by username or email
    if not target_users and clean_target:
        u_res = await session.execute(
            select(User).where(
                or_(
                    func.lower(User.username) == clean_target.lower(),
                    func.lower(User.email) == clean_target.lower(),
                )
            )
        )
        target_users = list(u_res.scalars().all())

    # 3. Try match by role name (e.g. "Student", "Parent", "Accountant", "Librarian", "Teacher", "Warden", "Staff", "All")
    if not target_users and (clean_target or payload.recipient_type):
        role_key = (clean_target or payload.recipient_type or "").upper()
        aud_map = {
            "ALL": None,
            "STUDENT": ["STUDENT"],
            "STUDENTS": ["STUDENT"],
            "PARENT": ["PARENT"],
            "PARENTS": ["PARENT"],
            "TEACHER": ["TEACHER"],
            "TEACHERS": ["TEACHER"],
            "ACCOUNTANT": ["ACCOUNTANT"],
            "ACCOUNTANTS": ["ACCOUNTANT"],
            "LIBRARIAN": ["LIBRARIAN"],
            "LIBRARIANS": ["LIBRARIAN"],
            "WARDEN": ["WARDEN"],
            "WARDENS": ["WARDEN"],
            "STAFF": ["TEACHER", "ACCOUNTANT", "LIBRARIAN", "WARDEN"],
        }
        
        if role_key in aud_map:
            target_roles = aud_map[role_key]
            if target_roles is None:
                # ALL users
                all_u = await session.execute(select(User).where(User.id != sender_id))
                target_users = list(all_u.scalars().all())
            else:
                role_u = await session.execute(
                    select(User).join(Role, User.role_id == Role.id).where(
                        func.upper(Role.role_name).in_(target_roles),
                        User.id != sender_id
                    )
                )
                target_users = list(role_u.scalars().all())

    # 4. Fallback if still empty: send to first other user
    if not target_users:
        fallback_u = await session.scalar(select(User).where(User.id != sender_id))
        if fallback_u:
            target_users.append(fallback_u)
        else:
            fallback_self = await session.get(User, sender_id)
            if fallback_self:
                target_users.append(fallback_self)

    first_msg = None
    for target in target_users:
        data = {
            "sender_id": sender_id,
            "receiver_id": target.id,
            "message": msg_text,
            "sent_on": payload.sent_on,
        }
        msg = await message_service.send_message(session, data)
        if first_msg is None:
            first_msg = msg

    return first_msg
@message_router.get("", response_model=list[MessageResponse])
async def get_messages(
    scope: str = Query("me", description="Scope of messages: 'me' for personal inbox, 'all' for admin system view"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if scope == "all" and current_user.role and current_user.role.role_name == "ADMIN":
        return await message_service.list(session)
    result = await session.execute(
        select(Message).where(
            or_(Message.sender_id == current_user.id, Message.receiver_id == current_user.id)
        )
    )
    return result.scalars().all()
@message_router.get("/conversation", response_model=list[MessageResponse])
async def get_conversation(sender_id: UUID, receiver_id: UUID, session: AsyncSession = Depends(get_db)): return await message_service.get_conversation(session, sender_id, receiver_id)
@message_router.get("/{item_id}", response_model=MessageResponse)
async def get_message(item_id: UUID, session: AsyncSession = Depends(get_db)): return await message_service.get(session, item_id)
@message_router.delete("/{item_id}")
async def delete_message(item_id: UUID, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await message_service.delete(session, item_id)
    return {"message": "Deleted successfully"}
@message_router.patch("/{item_id}/read", response_model=MessageResponse)
async def mark_message_read(item_id: UUID, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await message_service.mark_as_read(session, item_id)

user_communication_router = APIRouter()
@user_communication_router.get("/{user_id}/notifications", response_model=list[NotificationResponse])
async def user_notifications(user_id: UUID, session: AsyncSession = Depends(get_db)): return await notification_service.get_notifications(session, user_id)
@user_communication_router.get("/{user_id}/messages", response_model=list[MessageResponse])
async def user_messages(user_id: UUID, session: AsyncSession = Depends(get_db)): return await message_service.get_user_messages(session, user_id)


teacher_communication_router = APIRouter()
@teacher_communication_router.get("/teacher/{teacher_id}/messages", response_model=list[MessageResponse])
async def teacher_messages(teacher_id: UUID, session: AsyncSession = Depends(get_db)):
    return await message_service.get_user_messages(session, teacher_id)
