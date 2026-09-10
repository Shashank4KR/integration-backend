from app.api.v1.teachers.teachers import router as teacher_router
from app.api.v1.teachers.teacher_subjects import router as teacher_subject_router

__all__ = [
    "teacher_router",
    "teacher_subject_router",
]
