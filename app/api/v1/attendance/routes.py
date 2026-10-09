from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.models.parent_model import Parent
from app.models.parent_student_model import ParentStudent
from app.models.student_model import Student
from app.models.teacher_model import Teacher
from app.models.teacher_subject_model import TeacherSubject
from app.models.user import User
from app.schemas.attendance_schema import (
    AttendanceCreate,
    AttendanceResponse,
    AttendanceUpdate,
    BulkAttendanceCreate,
    ClassAttendanceSummary,
    StudentAttendanceReport,
    StudentAttendanceSummary,
    SubjectAttendanceSummary,
    TeacherAttendanceSummary,
)
from app.services.attendance_service import attendance_service

router = APIRouter()


def _ensure_teacher_or_admin(current_user: User) -> None:
    role_name = (current_user.role.role_name if current_user.role else "").upper()
    if role_name not in ("ADMIN", "TEACHER"):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or teacher users can perform this action",
        )


async def _get_current_teacher(session: AsyncSession, current_user: User) -> Teacher | None:
    role_name = current_user.role.role_name.upper() if current_user.role else ""
    if role_name != "TEACHER":
        return None
    result = await session.execute(select(Teacher).where(Teacher.user_id == current_user.id))
    teacher = result.scalar_one_or_none()
    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found",
        )
    return teacher


async def _ensure_teacher_context(
    session: AsyncSession,
    current_user: User,
    teacher_id: UUID,
    class_id: UUID | None = None,
    subject_id: UUID | None = None,
) -> None:
    role_name = current_user.role.role_name.upper() if current_user.role else ""
    if role_name == "ADMIN":
        return
    teacher = await _get_current_teacher(session, current_user)
    if teacher is None or teacher.id != teacher_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this teacher's attendance",
        )
    if class_id is not None and subject_id is not None:
        result = await session.execute(
            select(TeacherSubject).where(
                TeacherSubject.teacher_id == teacher.id,
                TeacherSubject.class_id == class_id,
                TeacherSubject.subject_id == subject_id,
            )
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teacher is not assigned to this class and subject",
            )


async def _ensure_student_access(
    session: AsyncSession,
    current_user: User,
    student_id: UUID,
) -> None:
    role_name = current_user.role.role_name.upper() if current_user.role else ""
    if role_name == "ADMIN":
        return
    if role_name == "TEACHER":
        teacher = await _get_current_teacher(session, current_user)
        result = await session.execute(
            select(TeacherSubject)
            .join(Student, Student.class_id == TeacherSubject.class_id)
            .where(TeacherSubject.teacher_id == teacher.id, Student.id == student_id)
        )
        if result.scalar_one_or_none() is not None:
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
        detail="You do not have permission to access this student's attendance",
    )


@router.post("", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
async def create_attendance(
    payload: AttendanceCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_teacher_or_admin(current_user)
    payload_data = payload.model_dump()
    payload_data["marked_by"] = current_user.id
    await _ensure_teacher_context(
        session,
        current_user,
        payload_data["teacher_id"],
        payload_data["class_id"],
        payload_data["subject_id"],
    )
    return await attendance_service.create_attendance(session, payload_data)


@router.post("/bulk", response_model=list[AttendanceResponse], status_code=status.HTTP_201_CREATED)
async def create_bulk_attendance(
    payload: BulkAttendanceCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_teacher_or_admin(current_user)
    payload_data = payload.model_dump()
    payload_data["marked_by"] = current_user.id
    await _ensure_teacher_context(
        session,
        current_user,
        payload_data["teacher_id"],
        payload_data["class_id"],
        payload_data["subject_id"],
    )
    return await attendance_service.create_bulk_attendance(session, payload_data)


@router.get("", response_model=list[AttendanceResponse])
async def get_all_attendance(
    class_id: UUID | None = Query(None),
    student_id: UUID | None = Query(None),
    teacher_id: UUID | None = Query(None),
    subject_id: UUID | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    status: str | None = Query(None),
    academic_year: str | None = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_teacher_or_admin(current_user)
    teacher = await _get_current_teacher(session, current_user)
    effective_teacher_id = teacher.id if teacher is not None else teacher_id
    return await attendance_service.get_all_attendance(
        session,
        class_id=class_id,
        student_id=student_id,
        teacher_id=effective_teacher_id,
        subject_id=subject_id,
        start_date=start_date,
        end_date=end_date,
        status=status,
        academic_year=academic_year,
    )


@router.get("/student/{student_id}", response_model=list[AttendanceResponse])
async def get_attendance_by_student(
    student_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_student_access(session, current_user, student_id)
    return await attendance_service.get_student_attendance(session, student_id)


@router.get("/teacher/{teacher_id}", response_model=list[AttendanceResponse])
async def get_attendance_by_teacher(
    teacher_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_teacher_context(session, current_user, teacher_id)
    return await attendance_service.get_teacher_attendance(session, teacher_id)


@router.get("/class/{class_id}", response_model=list[AttendanceResponse])
async def get_attendance_by_class(
    class_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_teacher_or_admin(current_user)
    teacher = await _get_current_teacher(session, current_user)
    if teacher is not None:
        result = await session.execute(
            select(TeacherSubject).where(
                TeacherSubject.teacher_id == teacher.id,
                TeacherSubject.class_id == class_id,
            )
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teacher is not assigned to this class",
            )
    return await attendance_service.get_class_attendance(session, class_id)


@router.get("/date/{attendance_date}", response_model=list[AttendanceResponse])
async def get_attendance_by_date(
    attendance_date: date,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_teacher_or_admin(current_user)
    teacher = await _get_current_teacher(session, current_user)
    if teacher is not None:
        records = await attendance_service.get_teacher_attendance(session, teacher.id)
        return [record for record in records if record.attendance_date == attendance_date]
    return await attendance_service.get_date_attendance(session, attendance_date)


@router.get("/student/{student_id}/report", response_model=StudentAttendanceReport)
async def get_student_report(
    student_id: UUID,
    start_date: date = Query(...),
    end_date: date = Query(...),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_student_access(session, current_user, student_id)
    records = await attendance_service.get_student_report(
        session, student_id, start_date, end_date
    )
    return {"student_id": student_id, "records": records}


@router.get("/student/{student_id}/summary", response_model=StudentAttendanceSummary)
async def get_student_summary(
    student_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_student_access(session, current_user, student_id)
    return await attendance_service.get_student_summary(session, student_id)


@router.get("/class/{class_id}/summary", response_model=ClassAttendanceSummary)
async def get_class_summary(
    class_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_teacher_or_admin(current_user)
    teacher = await _get_current_teacher(session, current_user)
    if teacher is not None:
        result = await session.execute(
            select(TeacherSubject).where(
                TeacherSubject.teacher_id == teacher.id,
                TeacherSubject.class_id == class_id,
            )
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teacher is not assigned to this class",
            )
    return await attendance_service.get_class_summary(session, class_id)


@router.get("/subject/{subject_id}/summary", response_model=SubjectAttendanceSummary)
async def get_subject_summary(
    subject_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_teacher_or_admin(current_user)
    teacher = await _get_current_teacher(session, current_user)
    if teacher is not None:
        result = await session.execute(
            select(TeacherSubject).where(
                TeacherSubject.teacher_id == teacher.id,
                TeacherSubject.subject_id == subject_id,
            )
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teacher is not assigned to this subject",
            )
    return await attendance_service.get_subject_summary(session, subject_id)


@router.get("/teacher/{teacher_id}/summary", response_model=TeacherAttendanceSummary)
async def get_teacher_summary(
    teacher_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_teacher_context(session, current_user, teacher_id)
    return await attendance_service.get_teacher_summary(session, teacher_id)


@router.get("/{attendance_id}", response_model=AttendanceResponse)
async def get_attendance(
    attendance_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attendance = await attendance_service.get_attendance(session, attendance_id)
    role_name = current_user.role.role_name.upper() if current_user.role else ""
    if role_name in ("ADMIN", "TEACHER"):
        await _ensure_teacher_context(
            session,
            current_user,
            attendance.teacher_id,
            attendance.class_id,
            attendance.subject_id,
        )
    else:
        await _ensure_student_access(session, current_user, attendance.student_id)
    return attendance


@router.put("/{attendance_id}", response_model=AttendanceResponse)
async def update_attendance(
    attendance_id: UUID,
    payload: AttendanceUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_teacher_or_admin(current_user)
    attendance = await attendance_service.get_attendance(session, attendance_id)
    await _ensure_teacher_context(
        session,
        current_user,
        attendance.teacher_id,
        attendance.class_id,
        attendance.subject_id,
    )
    return await attendance_service.update_attendance(
        session, attendance_id, payload.model_dump()
    )


@router.delete("/{attendance_id}", status_code=status.HTTP_200_OK)
async def delete_attendance(
    attendance_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_teacher_or_admin(current_user)
    attendance = await attendance_service.get_attendance(session, attendance_id)
    await _ensure_teacher_context(
        session,
        current_user,
        attendance.teacher_id,
        attendance.class_id,
        attendance.subject_id,
    )
    await attendance_service.delete_attendance(session, attendance_id)
    return {"message": "Deleted successfully"}
