from app.api.v1.users.admin import router as admin_router
from app.api.v1.users.routes import router as user_router

__all__ = [
    "admin_router",
    "user_router",
]
