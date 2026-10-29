import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.core.database import Base


class MarksConversionRule(Base):
    """A board-specific rule with an explicit source and verification trail."""

    __tablename__ = "marks_conversion_rules"
    __table_args__ = (
        Index(
            "ix_marks_rule_lookup",
            "board_direction",
            "state",
            "class_grade",
            "exam_type",
            "academic_year",
            "is_active",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    board_direction: Mapped[str] = mapped_column(String(32), nullable=False)
    state: Mapped[str] = mapped_column(String(80), nullable=False)
    class_grade: Mapped[str] = mapped_column(String(32), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(120), nullable=True)
    exam_type: Mapped[str] = mapped_column(String(80), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    source_max_marks: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    target_max_marks: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(32), nullable=False, default="PROPORTIONAL")
    source_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reference_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    is_official: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    verified_by_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class MarksConversionHistory(Base):
    """Persist a user's inputs and outcome for their private conversion history."""

    __tablename__ = "marks_conversion_history"
    __table_args__ = (Index("ix_marks_history_user_created", "user_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rule_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("marks_conversion_rules.id", ondelete="SET NULL"), nullable=True)
    board_direction: Mapped[str] = mapped_column(String(32), nullable=False)
    state: Mapped[str] = mapped_column(String(80), nullable=False)
    class_grade: Mapped[str] = mapped_column(String(32), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(120), nullable=True)
    exam_type: Mapped[str] = mapped_column(String(80), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    marks_obtained: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    source_max_marks: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    target_marks: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    target_max_marks: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    percentage: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(64), nullable=False)
    is_official: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    formula: Mapped[str] = mapped_column(String(255), nullable=False)
    source_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reference_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
