from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class _Response(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# Lesson Plan
class LessonPlanCreate(BaseModel):
    teacher_id: UUID
    class_id: UUID
    subject_id: UUID
    chapter_name: str = Field(..., min_length=1)
    topic: str = Field(..., min_length=1)
    plan_date: date = Field(default_factory=date.today)
    objectives: str | None = None
    materials_needed: str | None = None
    procedure_summary: str | None = None
    homework_notes: str | None = None
    status: str = Field(default="PUBLISHED")


class LessonPlanUpdate(BaseModel):
    chapter_name: str | None = None
    topic: str | None = None
    plan_date: date | None = None
    objectives: str | None = None
    materials_needed: str | None = None
    procedure_summary: str | None = None
    homework_notes: str | None = None
    status: str | None = None


class LessonPlanResponse(LessonPlanCreate, _Response):
    id: UUID
    created_at: datetime
    updated_at: datetime
    class_name: str | None = None
    subject_name: str | None = None
    teacher_name: str | None = None


# Content Resource / Links
class ContentResourceCreate(BaseModel):
    teacher_id: UUID
    class_id: UUID
    subject_id: UUID
    chapter_name: str | None = None
    title: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    description: str | None = None


class ContentResourceUpdate(BaseModel):
    chapter_name: str | None = None
    title: str | None = None
    url: str | None = None
    description: str | None = None


class ContentResourceResponse(ContentResourceCreate, _Response):
    id: UUID
    created_at: datetime
    updated_at: datetime
    class_name: str | None = None
    subject_name: str | None = None
    teacher_name: str | None = None


# Chapter Notes
class ChapterNoteCreate(BaseModel):
    teacher_id: UUID
    class_id: UUID
    subject_id: UUID
    chapter_name: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    file_url: str = Field(..., min_length=1)
    file_name: str = Field(..., min_length=1)
    file_size: int | None = None
    mime_type: str | None = None


class ChapterNoteUpdate(BaseModel):
    chapter_name: str | None = None
    title: str | None = None
    file_url: str | None = None
    file_name: str | None = None


class ChapterNoteResponse(ChapterNoteCreate, _Response):
    id: UUID
    created_at: datetime
    updated_at: datetime
    class_name: str | None = None
    subject_name: str | None = None
    teacher_name: str | None = None


# Student Feedback
class StudentFeedbackCreate(BaseModel):
    teacher_id: UUID
    student_id: UUID
    feedback_type: str = Field(default="ACADEMIC")
    comment: str = Field(..., min_length=1)
    feedback_date: date = Field(default_factory=date.today)


class StudentFeedbackUpdate(BaseModel):
    feedback_type: str | None = None
    comment: str | None = None
    feedback_date: date | None = None


class StudentFeedbackResponse(StudentFeedbackCreate, _Response):
    id: UUID
    created_at: datetime
    updated_at: datetime
    teacher_name: str | None = None
    student_name: str | None = None
