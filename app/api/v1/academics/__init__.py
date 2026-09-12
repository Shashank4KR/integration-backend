from app.api.v1.academics.academic_content import router as academic_content_router
from app.api.v1.academics.classes import router as class_router
from app.api.v1.academics.class_subjects import router as class_subject_router
from app.api.v1.academics.departments import router as department_router
from app.api.v1.academics.subjects import router as subject_router
from app.api.v1.academics.timetable import router as timetable_router

__all__ = [
    "academic_content_router",
    "class_router",
    "class_subject_router",
    "department_router",
    "subject_router",
    "timetable_router",
]
