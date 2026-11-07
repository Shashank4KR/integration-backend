from app.schemas.academic_content_schema import (
    ChapterNoteCreate,
    ChapterNoteResponse,
    ChapterNoteUpdate,
    ContentResourceCreate,
    ContentResourceResponse,
    ContentResourceUpdate,
    LessonPlanCreate,
    LessonPlanResponse,
    LessonPlanUpdate,
    StudentFeedbackCreate,
    StudentFeedbackResponse,
    StudentFeedbackUpdate,
)
from app.schemas.faculty import (
    FacultyCreate,
    FacultyResponse,
    FacultyUpdate,
)
from app.schemas.parent import (
    ParentCreate,
    ParentResponse,
    ParentUpdate,
)
from app.schemas.student import (
    StudentCreate,
    StudentResponse,
    StudentUpdate,
)

__all__ = [
    "LessonPlanCreate",
    "LessonPlanUpdate",
    "LessonPlanResponse",
    "ContentResourceCreate",
    "ContentResourceUpdate",
    "ContentResourceResponse",
    "ChapterNoteCreate",
    "ChapterNoteUpdate",
    "ChapterNoteResponse",
    "StudentFeedbackCreate",
    "StudentFeedbackUpdate",
    "StudentFeedbackResponse",
    "StudentCreate",
    "StudentUpdate",
    "StudentResponse",
    "ParentCreate",
    "ParentUpdate",
    "ParentResponse",
    "FacultyCreate",
    "FacultyUpdate",
    "FacultyResponse",
]
