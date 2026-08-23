from app.schemas.academic_content_schema import (
    LessonPlanCreate,
    LessonPlanUpdate,
    LessonPlanResponse,
    ContentResourceCreate,
    ContentResourceUpdate,
    ContentResourceResponse,
    ChapterNoteCreate,
    ChapterNoteUpdate,
    ChapterNoteResponse,
    StudentFeedbackCreate,
    StudentFeedbackUpdate,
    StudentFeedbackResponse,
)

from app.schemas.student import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
)

from app.schemas.parent import (
    ParentCreate,
    ParentUpdate,
    ParentResponse,
)

from app.schemas.faculty import (
    FacultyCreate,
    FacultyUpdate,
    FacultyResponse,
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
