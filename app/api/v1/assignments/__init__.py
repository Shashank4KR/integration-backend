from app.api.v1.assignments.routes import (
    class_assignment_router,
    router,
    student_assignment_router,
    submission_router,
    teacher_assignment_router,
)

__all__ = [
    "router",
    "submission_router",
    "teacher_assignment_router",
    "class_assignment_router",
    "student_assignment_router",
]
