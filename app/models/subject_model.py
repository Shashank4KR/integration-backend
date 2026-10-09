import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    subject_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    subject_name: Mapped[str] = mapped_column(String(255), nullable=False)
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True
    )
    subject_type: Mapped[str | None] = mapped_column(String(50), default="THEORY", nullable=True)
    credits: Mapped[int | None] = mapped_column(Integer, default=3, nullable=True)
    periods_per_week: Mapped[int | None] = mapped_column(Integer, default=4, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False, server_default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    department = relationship("Department", lazy="selectin")

    class_subjects = relationship(
        "ClassSubject", back_populates="subject", cascade="all, delete-orphan"
    )
    teacher_subjects = relationship(
        "TeacherSubject", back_populates="subject", cascade="all, delete-orphan"
    )
    assignments = relationship("Assignment", back_populates="subject", cascade="all, delete-orphan")
    timetables = relationship(
        "Timetable", back_populates="subject", cascade="all, delete-orphan"
    )
    attendance_records = relationship(
        "Attendance", back_populates="subject", cascade="all, delete-orphan"
    )
    exam_results = relationship(
        "ExamResult", back_populates="subject", cascade="all, delete-orphan"
    )
