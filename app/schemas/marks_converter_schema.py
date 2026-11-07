from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator, model_validator
from app.schemas.base import BaseSchema


class BoardDirection(str, Enum):
    CBSE_TO_STATE = "CBSE_TO_STATE"
    STATE_TO_CBSE = "STATE_TO_CBSE"
    ICSE_TO_CBSE = "ICSE_TO_CBSE"
    CBSE_TO_ICSE = "CBSE_TO_ICSE"
    ICSE_TO_STATE = "ICSE_TO_STATE"
    STATE_TO_ICSE = "STATE_TO_ICSE"


class MarksConversionRequest(BaseSchema):
    board_direction: BoardDirection
    state: str = Field(min_length=2, max_length=80)
    class_grade: str = Field(min_length=1, max_length=32)
    subject: str | None = Field(default=None, max_length=120)
    exam_type: str = Field(min_length=1, max_length=80)
    academic_year: str = Field(min_length=4, max_length=20)
    marks_obtained: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    source_max_marks: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    target_max_marks: Decimal = Field(gt=0, max_digits=10, decimal_places=2)

    @field_validator("state", "class_grade", "exam_type", "academic_year", mode="before")
    @classmethod
    def trim_required_labels(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("subject", mode="before")
    @classmethod
    def trim_subject(cls, value):
        return value.strip() or None if isinstance(value, str) else value

    @model_validator(mode="after")
    def obtained_marks_fit_source_maximum(self):
        if self.marks_obtained > self.source_max_marks:
            raise ValueError("Marks obtained cannot exceed the source maximum marks")
        return self


class MarksConversionRuleCreate(BaseSchema):
    board_direction: BoardDirection
    state: str = Field(min_length=2, max_length=80)
    class_grade: str = Field(min_length=1, max_length=32)
    subject: str | None = Field(default=None, max_length=120)
    exam_type: str = Field(min_length=1, max_length=80)
    academic_year: str = Field(min_length=4, max_length=20)
    source_max_marks: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    target_max_marks: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    method: str = Field(default="PROPORTIONAL", pattern="^PROPORTIONAL$")
    source_title: str | None = Field(default=None, max_length=255)
    reference_url: AnyHttpUrl | None = None
    is_official: bool = False
    is_active: bool = True

    @field_validator("state", "class_grade", "exam_type", "academic_year", mode="before")
    @classmethod
    def trim_required_labels(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("subject", "source_title", mode="before")
    @classmethod
    def trim_optional_labels(cls, value):
        return value.strip() or None if isinstance(value, str) else value

    @model_validator(mode="after")
    def official_rule_requires_source(self):
        if self.is_official and (not self.source_title or not self.reference_url):
            raise ValueError("Official rules require a document title and reference URL")
        return self


class MarksConversionRuleUpdate(BaseSchema):
    board_direction: BoardDirection | None = None
    state: str | None = Field(default=None, min_length=2, max_length=80)
    class_grade: str | None = Field(default=None, min_length=1, max_length=32)
    subject: str | None = Field(default=None, max_length=120)
    exam_type: str | None = Field(default=None, min_length=1, max_length=80)
    academic_year: str | None = Field(default=None, min_length=4, max_length=20)
    source_max_marks: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    target_max_marks: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    method: str | None = Field(default=None, pattern="^PROPORTIONAL$")
    source_title: str | None = Field(default=None, max_length=255)
    reference_url: AnyHttpUrl | None = None
    is_official: bool | None = None
    is_active: bool | None = None


class MarksConversionRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    board_direction: BoardDirection
    state: str
    class_grade: str
    subject: str | None
    exam_type: str
    academic_year: str
    source_max_marks: Decimal
    target_max_marks: Decimal
    method: str
    source_title: str | None
    reference_url: str | None
    is_official: bool
    is_active: bool
    verified_by_id: UUID | None
    verified_at: datetime | None
    created_at: datetime
    updated_at: datetime


class MarksConversionResult(BaseModel):
    history_id: UUID
    board_direction: BoardDirection
    source_board: str
    target_board: str
    state: str
    class_grade: str
    subject: str | None
    marks_obtained: Decimal
    source_max_marks: Decimal
    target_marks: Decimal
    target_max_marks: Decimal
    percentage: Decimal
    method: str
    formula: str
    is_official: bool
    status_note: str
    source_title: str | None = None
    reference_url: str | None = None
    created_at: datetime
