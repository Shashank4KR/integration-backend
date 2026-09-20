import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )
    employee_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    qualification: Mapped[str | None] = mapped_column(String(255), nullable=True)
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True
    )
    join_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="teacher", lazy="selectin")
    department = relationship("Department", back_populates="teachers", lazy="selectin")
    classes = relationship("Class", back_populates="class_teacher", lazy="selectin")
    teacher_subjects = relationship(
        "TeacherSubject", back_populates="teacher", cascade="all, delete-orphan"
    )
    timetables = relationship(
        "Timetable", back_populates="teacher", cascade="all, delete-orphan"
    )
    attendance_records = relationship(
        "Attendance", back_populates="teacher", cascade="all, delete-orphan"
    )
    assignments = relationship("Assignment", back_populates="teacher", cascade="all, delete-orphan")
