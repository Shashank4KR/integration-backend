import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.audit_model import AuditLog
from app.models.class_subject_model import ClassSubject
from app.models.exam_model import Exam
from app.models.exam_models import ExamSubject
from app.models.exam_result_model import ExamResult
from app.models.student_model import Student
from app.models.teacher_model import Teacher
from app.models.teacher_subject_model import TeacherSubject
from app.models.user import User
from app.schemas.exam_schema import (
    ExamResultAuditOverride,
    ExamResultCreate,
    ExamResultResponse,
    ExamResultUpdate,
)
from app.schemas.student_schema import StudentResponse
from app.services.exam_result_service import exam_result_service
from app.services.ownership_service import check_teacher_ownership

router = APIRouter()


def _ensure_teacher_only(current_user: User) -> None:
    role_name = (current_user.role.role_name if current_user.role else "").upper()
    if role_name != "TEACHER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teacher users can perform this action",
        )


def _ensure_admin_only(current_user: User) -> None:
    role_name = (current_user.role.role_name if current_user.role else "").upper()
    if role_name not in ("ADMIN", "SUPER_ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for audit override",
        )


async def _get_current_teacher(session: AsyncSession, current_user: User) -> Teacher:
    result = await session.execute(select(Teacher).where(Teacher.user_id == current_user.id))
    teacher = result.scalar_one_or_none()
    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher profile not found",
        )
    return teacher


async def _ensure_teacher_subject_assignment(
    session: AsyncSession,
    teacher_id: UUID,
    class_id: UUID,
    subject_id: UUID,
) -> None:
    result = await session.execute(
        select(TeacherSubject).where(
            TeacherSubject.teacher_id == teacher_id,
            TeacherSubject.class_id == class_id,
            TeacherSubject.subject_id == subject_id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher is not assigned to this class and subject",
        )


async def _ensure_exam_covers_subject_and_class(
    session: AsyncSession,
    exam_id: UUID,
    class_id: UUID,
    subject_id: UUID,
) -> Exam:
    exam = await session.get(Exam, exam_id)
    if exam is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")
    if exam.class_id != class_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student does not belong to exam class",
        )
    exam_sub = await session.execute(
        select(ExamSubject).where(
            ExamSubject.exam_id == exam_id,
            ExamSubject.subject_id == subject_id,
        )
    )
    class_sub = await session.execute(
        select(ClassSubject).where(
            ClassSubject.class_id == class_id,
            ClassSubject.subject_id == subject_id,
        )
    )
    if exam_sub.scalar_one_or_none() is None and class_sub.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subject is not part of this exam",
        )
    return exam


def _check_marks_correction_window(result: ExamResult) -> None:
    now = datetime.now(timezone.utc)
    created = result.created_at
    if created is not None:
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        cutoff = created + timedelta(hours=settings.MARKS_CORRECTION_WINDOW_HOURS)
        if now > cutoff:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Marks correction window ({settings.MARKS_CORRECTION_WINDOW_HOURS} hours) has expired.",
            )


@router.post("", response_model=ExamResultResponse, status_code=status.HTTP_201_CREATED)
async def create_exam_result(
    payload: ExamResultCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_teacher_only(current_user)
    teacher = await _get_current_teacher(session, current_user)
    student = await session.get(Student, payload.student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    await _ensure_exam_covers_subject_and_class(
        session, payload.exam_id, student.class_id, payload.subject_id
    )
    await _ensure_teacher_subject_assignment(
        session, teacher.id, student.class_id, payload.subject_id
    )
    payload_data = payload.model_dump()
    payload_data["entered_by"] = current_user.id
    return await exam_result_service.create(session, payload_data)


@router.get("", response_model=list[ExamResultResponse])
async def list_exam_results(session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await exam_result_service.list(session)


@router.get("/{item_id}", response_model=ExamResultResponse)
async def get_exam_result(item_id: UUID, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await exam_result_service.get(session, item_id)


@router.put("/{item_id}", response_model=ExamResultResponse)
async def update_exam_result(
    item_id: UUID,
    payload: ExamResultUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_teacher_only(current_user)
    teacher = await _get_current_teacher(session, current_user)
    result = await exam_result_service.get(session, item_id)
    if result.entered_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit exam results that you entered",
        )
    exam = await session.get(Exam, result.exam_id)
    if exam:
        await _ensure_teacher_subject_assignment(
            session, teacher.id, exam.class_id, result.subject_id
        )
    _check_marks_correction_window(result)
    return await exam_result_service.update(session, item_id, payload.model_dump(exclude_unset=True))


@router.delete("/{item_id}", status_code=status.HTTP_200_OK)
async def delete_exam_result(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_teacher_only(current_user)
    teacher = await _get_current_teacher(session, current_user)
    result = await exam_result_service.get(session, item_id)
    if result.entered_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete exam results that you entered",
        )
    exam = await session.get(Exam, result.exam_id)
    if exam:
        await _ensure_teacher_subject_assignment(
            session, teacher.id, exam.class_id, result.subject_id
        )
    _check_marks_correction_window(result)
    await exam_result_service.delete(session, item_id)
    return {"message": "Deleted successfully"}


@router.post("/{item_id}/audit-override", response_model=ExamResultResponse)
async def audit_override_exam_result(
    item_id: UUID,
    payload: ExamResultAuditOverride,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_only(current_user)
    if len(payload.reason.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reason must be at least 10 characters long",
        )
    result = await exam_result_service.get(session, item_id)
    exam = await session.get(Exam, result.exam_id)
    if exam is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")
    if payload.marks_obtained < 0 or payload.marks_obtained > exam.max_marks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"marks_obtained must be between 0 and exam max_marks ({exam.max_marks})",
        )

    old_value = {
        "marks_obtained": str(result.marks_obtained),
        "grade": result.grade,
        "remarks": result.remarks,
    }
    new_grade = exam_result_service._calculate_grade(payload.marks_obtained, exam.max_marks)
    new_value = {
        "marks_obtained": str(payload.marks_obtained),
        "grade": new_grade,
        "remarks": payload.remarks,
    }

    result.marks_obtained = payload.marks_obtained
    result.grade = new_grade
    if payload.remarks is not None:
        result.remarks = payload.remarks

    audit_entry = AuditLog(
        user_id=current_user.id,
        activity="EXAM_RESULT_AUDIT_OVERRIDE",
        details=json.dumps({
            "record_id": str(item_id),
            "old_value": old_value,
            "new_value": new_value,
            "admin_id": str(current_user.id),
            "reason": payload.reason.strip(),
        }),
    )
    session.add(audit_entry)
    await session.commit()
    await session.refresh(result)
    return result


@router.get("/teacher/{teacher_id}/students", response_model=list[StudentResponse])
async def get_teacher_students(
    teacher_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await check_teacher_ownership(session, current_user, teacher_id)
    from app.models.teacher_subject_model import TeacherSubject
    result = await session.execute(
        select(Student)
        .join(TeacherSubject, TeacherSubject.class_id == Student.class_id)
        .where(TeacherSubject.teacher_id == teacher_id)
        .distinct()
    )
    return result.scalars().all()

