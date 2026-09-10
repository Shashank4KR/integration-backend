from app.api.v1.parents.parents import router as parent_router
from app.api.v1.parents.parent_students import router as parent_student_router

__all__ = [
    "parent_router",
    "parent_student_router",
]
