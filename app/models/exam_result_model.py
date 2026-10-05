import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ExamResult(Base):
    __tablename__ = "exam_results"
    __table_args__ = (UniqueConstraint("exam_id", "student_id", "subject_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    exam_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exams.id"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False
    )
    marks_obtained: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    grade: Mapped[str | None] = mapped_column(String(10), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    entered_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    exam = relationship("Exam", back_populates="results", lazy="selectin")
    student = relationship("Student", back_populates="exam_results", lazy="selectin")
    subject = relationship("Subject", back_populates="exam_results", lazy="selectin")
    entered_by_user = relationship("User", foreign_keys=[entered_by], lazy="selectin")
