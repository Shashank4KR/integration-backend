import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.attendance_model import Attendance
    from app.models.audit_model import AuditLog, LoginHistory
    from app.models.ai_analytics_model import AIChatHistory
    from app.models.admin_model import Admin
    from app.models.parent_model import Parent
    from app.models.role import Role
    from app.models.student_model import Student
    from app.models.teacher_model import Teacher


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    role: Mapped["Role"] = relationship(
        back_populates="users",
        lazy="selectin",
    )
    admin: Mapped["Admin | None"] = relationship(back_populates="user", uselist=False)
    teacher: Mapped["Teacher | None"] = relationship(back_populates="user", uselist=False)
    parent: Mapped["Parent | None"] = relationship(back_populates="user", uselist=False)
    student: Mapped["Student | None"] = relationship(back_populates="user", uselist=False)
    marked_attendance: Mapped[list["Attendance"]] = relationship(
        back_populates="marked_by_user"
    )
    announcements = relationship("Announcement", back_populates="creator", foreign_keys="Announcement.created_by")
    notifications = relationship("Notification", back_populates="user")
    sent_messages = relationship("Message", back_populates="sender", foreign_keys="Message.sender_id")
    received_messages = relationship("Message", back_populates="receiver", foreign_keys="Message.receiver_id")
    events_created = relationship("Event", back_populates="creator", foreign_keys="Event.created_by")
    verified_documents = relationship(
        "AdmissionDocument",
        back_populates="verifier",
        foreign_keys="AdmissionDocument.verified_by",
    )
    leave_requests = relationship(
        "LeaveRequest",
        back_populates="applicant",
        foreign_keys="LeaveRequest.user_id",
        cascade="all, delete-orphan",
    )
    approved_leave_requests = relationship(
        "LeaveRequest",
        back_populates="approver",
        foreign_keys="LeaveRequest.approved_by",
    )
    login_history: Mapped[list["LoginHistory"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    ai_chat_history: Mapped[list["AIChatHistory"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    hostel_blocks = relationship("HostelBlock", back_populates="warden", foreign_keys="HostelBlock.warden_id")
    approved_hostel_visitors = relationship("HostelVisitor", back_populates="approver", foreign_keys="HostelVisitor.approved_by")
    assigned_hostel_complaints = relationship("HostelComplaint", back_populates="assignee", foreign_keys="HostelComplaint.assigned_to")
    resolved_hostel_complaints = relationship("HostelComplaint", back_populates="resolver", foreign_keys="HostelComplaint.resolved_by")
    approved_hostel_leave_requests = relationship("HostelLeaveRequest", back_populates="approver", foreign_keys="HostelLeaveRequest.approved_by")
    hostel_notices = relationship("HostelNotice", back_populates="publisher", foreign_keys="HostelNotice.published_by")

    @property
    def is_active(self) -> bool:
        return self.status

    @is_active.setter
    def is_active(self, value: bool) -> None:
        self.status = value
