from typing import Any
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.class_model import Class
from app.models.parent_model import Parent
from app.models.parent_student_model import ParentStudent
from app.models.student_model import Student
from app.models.teacher_model import Teacher
from app.models.teacher_subject_model import TeacherSubject
from app.models.user import User


def _user_role(user: User) -> str:
    return (user.role.role_name if user.role else "").upper()


def check_user_ownership(current_user: User, target_user_id: UUID | str) -> None:
    """Verifies that a user can only access their own user record unless ADMIN."""
    if _user_role(current_user) == "ADMIN":
        return
    if str(current_user.id) != str(target_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you can only access your own user account",
        )


async def check_student_ownership(
    session: AsyncSession, current_user: User, student_id: UUID | str
) -> Student:
    """
    Verifies student resource access:
    - ADMIN / ACCOUNTANT / LIBRARIAN: Allowed across school.
    - STUDENT: Only their own student profile.
    - PARENT: Only linked children (via ParentStudent).
    - TEACHER: Only students in their assigned classes.
    """
    sid = UUID(str(student_id))
    result = await session.execute(select(Student).where(Student.id == sid))
    student = result.scalar_one_or_none()
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    role = _user_role(current_user)
    if role in ("ADMIN", "ACCOUNTANT", "LIBRARIAN"):

        return student

    if role == "STUDENT":
        if str(student.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: students can only access their own record",
            )
        return student

    if role == "PARENT":
        p_res = await session.execute(select(Parent).where(Parent.user_id == current_user.id))
        parent = p_res.scalar_one_or_none()
        if parent:
            link = await session.execute(
                select(ParentStudent).where(
                    ParentStudent.parent_id == parent.id,
                    ParentStudent.student_id == student.id,
                )
            )
            if link.scalar_one_or_none():
                return student
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: parents can only access their linked children's records",
        )

    if role == "TEACHER":
        t_res = await session.execute(select(Teacher).where(Teacher.user_id == current_user.id))
        teacher = t_res.scalar_one_or_none()
        if teacher and student.class_id:
            cls_res = await session.execute(
                select(Class).where(
                    Class.id == student.class_id,
                    Class.class_teacher_id == teacher.id,
                )
            )
            if cls_res.scalar_one_or_none():
                return student
            ts_res = await session.execute(
                select(TeacherSubject).where(
                    TeacherSubject.teacher_id == teacher.id,
                    TeacherSubject.class_id == student.class_id,
                )
            )
            if ts_res.scalar_one_or_none():
                return student
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: teachers can only access students in their assigned classes",
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied for current user role",
    )


async def check_teacher_ownership(
    session: AsyncSession, current_user: User, teacher_id: UUID | str
) -> Teacher:
    """Verifies teacher resource access: TEACHER can only access own data; ADMIN any."""
    tid = UUID(str(teacher_id))
    result = await session.execute(select(Teacher).where(Teacher.id == tid))
    teacher = result.scalar_one_or_none()
    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found",
        )

    role = _user_role(current_user)
    if role in ("ADMIN", "ACCOUNTANT", "LIBRARIAN"):
        return teacher

    if role == "TEACHER":
        if str(teacher.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: teachers can only access their own records",
            )
        return teacher

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied for current user role",
    )


def check_notification_ownership(current_user: User, notification: Any) -> None:
    if _user_role(current_user) == "ADMIN":
        return
    if str(getattr(notification, "user_id", None)) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you can only access your own notifications",
        )


def check_message_ownership(current_user: User, message: Any) -> None:
    if _user_role(current_user) == "ADMIN":
        return
    sender_id = getattr(message, "sender_id", None)
    receiver_id = getattr(message, "receiver_id", None)
    if str(current_user.id) not in (str(sender_id), str(receiver_id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you can only access messages in your own conversations",
        )


def check_leave_ownership(current_user: User, leave: Any) -> None:
    role = _user_role(current_user)
    if role in ("ADMIN", "TEACHER"):
        return
    if str(getattr(leave, "user_id", None)) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you can only access your own leave requests",
        )
