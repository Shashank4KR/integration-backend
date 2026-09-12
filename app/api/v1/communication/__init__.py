from app.api.v1.communication.routes import (
    announcement_router,
    communication_router,
    message_router,
    notification_router,
    teacher_communication_router,
    user_communication_router,
)

__all__ = [
    "announcement_router",
    "notification_router",
    "message_router",
    "communication_router",
    "user_communication_router",
    "teacher_communication_router",
]
