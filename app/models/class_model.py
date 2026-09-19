import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Class(Base):
    __tablename__ = "classes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    class_name: Mapped[str] = mapped_column(String(100), nullable=False)
    section: Mapped[str] = mapped_column(String(50), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    class_teacher_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teachers.id"), nullable=True
    )
    room_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str | None] = mapped_column(
        String(20), nullable=True, default="ACTIVE", server_default="ACTIVE"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    class_teacher = relationship("Teacher", back_populates="classes", lazy="selectin")
    class_subjects = relationship(
        "ClassSubject", back_populates="class_", cascade="all, delete-orphan"
    )
    teacher_subjects = relationship(
        "TeacherSubject", back_populates="class_", cascade="all, delete-orphan"
    )
    timetables = relationship(
        "Timetable", back_populates="class_", cascade="all, delete-orphan"
    )
    students = relationship("Student", back_populates="class_", lazy="selectin")
    attendance_records = relationship(
        "Attendance", back_populates="class_", cascade="all, delete-orphan"
    )
    exams = relationship("Exam", back_populates="class_", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="class_", cascade="all, delete-orphan")
    admission_applications = relationship(
        "AdmissionApplication",
        back_populates="class_",
        cascade="all, delete-orphan",
    )
