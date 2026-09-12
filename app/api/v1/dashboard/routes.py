from datetime import date
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

import app.models.attendance_model
import app.models.class_model
import app.models.library_model
import app.models.subject_model
import app.models.teacher_subject_model
import app.models.timetable_model
from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.models.class_model import Class
from app.models.event_model import Event
from app.models.fee_model import FeeInvoice, Payment
from app.models.parent_model import Parent
from app.models.parent_student_model import ParentStudent
from app.models.student_model import Student
from app.models.subject_model import Subject
from app.models.teacher_model import Teacher
from app.models.user import User

router = APIRouter()


def _ensure_admin(current_user: User) -> None:
    if current_user.role.role_name != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can access dashboard stats",
        )


async def _ensure_teacher_access(session: AsyncSession, current_user: User, teacher_id: UUID) -> None:
    role_name = current_user.role.role_name.upper() if current_user.role else ""
    if role_name == "ADMIN":
        return
    if role_name == "TEACHER":
        result = await session.execute(
            select(Teacher).where(Teacher.id == teacher_id, Teacher.user_id == current_user.id)
        )
        if result.scalar_one_or_none() is not None:
            return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to access this teacher's records",
    )


async def _ensure_student_access(session: AsyncSession, current_user: User, student_id: UUID) -> None:
    role_name = current_user.role.role_name.upper() if current_user.role else ""
    if role_name == "ADMIN":
        return
    if role_name == "STUDENT":
        result = await session.execute(
            select(Student).where(Student.id == student_id, Student.user_id == current_user.id)
        )
        if result.scalar_one_or_none() is not None:
            return
    if role_name == "PARENT":
        result = await session.execute(
            select(ParentStudent)
            .join(Parent, Parent.id == ParentStudent.parent_id)
            .where(Parent.user_id == current_user.id, ParentStudent.student_id == student_id)
        )
        if result.scalar_one_or_none() is not None:
            return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to access this student's records",
    )


@router.get("/stats")
async def get_dashboard_stats(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)

    student_count = (await session.execute(select(func.count(Student.id)))).scalar() or 0
    teacher_count = (await session.execute(select(func.count(Teacher.id)))).scalar() or 0
    class_count = (await session.execute(select(func.count(Class.id)))).scalar() or 0
    subject_count = (await session.execute(select(func.count(Subject.id)))).scalar() or 0

    total_invoiced = (
        await session.execute(select(func.coalesce(func.sum(FeeInvoice.amount), 0)))
    ).scalar() or 0
    total_paid = (
        await session.execute(select(func.coalesce(func.sum(Payment.amount_paid), 0)))
    ).scalar() or 0

    today = date.today()
    month_start = today.replace(day=1)
    today_collection = await session.scalar(
        select(func.coalesce(func.sum(Payment.amount_paid), 0)).where(
            Payment.payment_date == today
        )
    ) or 0
    monthly_collection = await session.scalar(
        select(func.coalesce(func.sum(Payment.amount_paid), 0)).where(
            Payment.payment_date >= month_start
        )
    ) or 0

    outstanding = float(total_invoiced) - float(total_paid)

    upcoming_events = (
        await session.execute(
            select(func.count(Event.id)).where(Event.start_date >= func.current_date())
        )
    ).scalar() or 0

    return {
        "total_students": student_count,
        "total_teachers": teacher_count,
        "total_classes": class_count,
        "total_subjects": subject_count,
        "total_fees_invoiced": float(total_invoiced),
        "total_fees_collected": float(total_paid),
        "upcoming_events": upcoming_events,
        "today_collection": float(today_collection),
        "monthly_collection": float(monthly_collection),
        "outstanding_fees": float(outstanding),
    }


@router.get("/teacher/{teacher_id}")
async def get_teacher_dashboard(
    teacher_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.role_name not in ("ADMIN", "TEACHER"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or teacher users can access this dashboard",
        )

    await _ensure_teacher_access(session, current_user, teacher_id)

    teacher = await session.execute(select(Teacher).where(Teacher.id == teacher_id))
    teacher_obj = teacher.scalar_one_or_none()
    if teacher_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found",
        )

    classes_result = await session.execute(
        select(func.count(func.distinct(Class.id)))
        .select_from(Class)
        .join(app.models.timetable_model.Timetable, app.models.timetable_model.Timetable.class_id == Class.id)
        .where(app.models.timetable_model.Timetable.teacher_id == teacher_id)
    )
    assigned_classes = classes_result.scalar() or 0

    subjects_result = await session.execute(
        select(func.count(func.distinct(app.models.subject_model.Subject.id)))
        .select_from(app.models.subject_model.Subject)
        .join(app.models.teacher_subject_model.TeacherSubject, app.models.teacher_subject_model.TeacherSubject.subject_id == app.models.subject_model.Subject.id)
        .where(app.models.teacher_subject_model.TeacherSubject.teacher_id == teacher_id)
    )
    assigned_subjects = subjects_result.scalar() or 0

    students_result = await session.execute(
        select(func.count(func.distinct(app.models.student_model.Student.id)))
        .select_from(app.models.student_model.Student)
        .join(app.models.class_model.Class, app.models.class_model.Class.id == app.models.student_model.Student.class_id)
        .join(app.models.timetable_model.Timetable, app.models.timetable_model.Timetable.class_id == app.models.class_model.Class.id)
        .where(app.models.timetable_model.Timetable.teacher_id == teacher_id)
    )
    total_students = students_result.scalar() or 0

    return {
        "assigned_classes": assigned_classes,
        "assigned_subjects": assigned_subjects,
        "total_students": total_students,
        "teacher_name": f"{teacher_obj.user.username if teacher_obj.user else ''}",
    }


@router.get("/student/{student_id}")
async def get_student_dashboard(
    student_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.role_name not in ("ADMIN", "STUDENT", "PARENT"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin, student, or parent users can access this dashboard",
        )

    await _ensure_student_access(session, current_user, student_id)

    student = await session.execute(select(Student).where(Student.id == student_id))
    student_obj = student.scalar_one_or_none()
    if student_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    attendance_result = await session.execute(
        select(func.count(app.models.attendance_model.Attendance.id))
        .where(app.models.attendance_model.Attendance.student_id == student_id)
    )
    total_attendance = attendance_result.scalar() or 0

    present_result = await session.execute(
        select(func.count(app.models.attendance_model.Attendance.id))
        .where(app.models.attendance_model.Attendance.student_id == student_id)
        .where(app.models.attendance_model.Attendance.status == "PRESENT")
    )
    present_attendance = present_result.scalar() or 0

    attendance_percentage = (present_attendance / total_attendance * 100) if total_attendance > 0 else 0

    fees_result = await session.execute(
        select(func.coalesce(func.sum(FeeInvoice.amount), 0))
        .where(FeeInvoice.student_id == student_id)
    )
    total_fees = fees_result.scalar() or 0

    paid_result = await session.execute(
        select(func.coalesce(func.sum(Payment.amount_paid), 0))
        .select_from(Payment)
        .join(FeeInvoice, FeeInvoice.id == Payment.invoice_id)
        .where(FeeInvoice.student_id == student_id)
    )
    paid_fees = paid_result.scalar() or 0

    return {
        "attendance_percentage": round(attendance_percentage, 2),
        "total_classes": total_attendance,
        "present": present_attendance,
        "total_fees": float(total_fees),
        "paid_amount": float(paid_fees),
        "pending_amount": float(total_fees - paid_fees),
        "student_name": f"{student_obj.first_name or ''} {student_obj.last_name or ''}".strip() or student_obj.admission_no,
    }


@router.get("/librarian")
async def get_librarian_dashboard(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.role_name not in ("ADMIN", "LIBRARIAN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or librarian users can access this dashboard",
        )

    total_books = (await session.execute(select(func.count(app.models.library_model.Book.id)))).scalar() or 0
    total_issued = (await session.execute(
        select(func.count(app.models.library_model.BookIssue.id))
        .where(app.models.library_model.BookIssue.status == app.models.library_model.BookIssueStatus.ISSUED.value)
    )).scalar() or 0
    total_overdue = (await session.execute(
        select(func.count(app.models.library_model.BookIssue.id))
        .where(app.models.library_model.BookIssue.status == app.models.library_model.BookIssueStatus.OVERDUE.value)
    )).scalar() or 0

    return {
        "total_books": total_books,
        "total_issued": total_issued,
        "total_overdue": total_overdue,
    }
