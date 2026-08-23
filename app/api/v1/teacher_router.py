from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.api.v1.router_factory import build_crud_router
from app.core.database import get_db
from app.models.assignment_model import Assignment, AssignmentSubmission
from app.models.class_model import Class
from app.models.communication_model import Message
from app.models.event_model import Event
from app.models.exam_result_model import ExamResult
from app.models.exam_model import Exam
from app.models.student_model import Student
from app.models.subject_model import Subject
from app.models.teacher_model import Teacher
from app.models.teacher_subject_model import TeacherSubject
from app.models.timetable_model import Timetable
from app.models.user import User
from app.schemas.class_schema import ClassResponse
from app.schemas.subject_schema import SubjectResponse
from app.schemas.teacher_schema import TeacherCreate, TeacherResponse, TeacherUpdate
from app.services.teacher_service import teacher_service

router = build_crud_router(teacher_service, TeacherCreate, TeacherUpdate, TeacherResponse)


def _ensure_admin(current_user: User) -> None:
    if current_user.role.role_name != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can perform this action",
        )


async def _ensure_teacher_access(
    teacher_id: UUID,
    session: AsyncSession,
    current_user: User,
) -> None:
    role_name = current_user.role.role_name.upper() if current_user.role else ""
    if role_name == "ADMIN":
        await teacher_service.get(session, teacher_id)
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


@router.post("", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
async def create_teacher(
    payload: TeacherCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    return await teacher_service.create(session, payload.model_dump())


@router.put("/{item_id}", response_model=TeacherResponse)
async def update_teacher(
    item_id: UUID,
    payload: TeacherUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    return await teacher_service.update(session, item_id, payload.model_dump(exclude_unset=True))


@router.delete("/{item_id}")
async def delete_teacher(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    await teacher_service.delete(session, item_id)
    return {"message": "Deleted successfully"}


@router.get("/{teacher_id}/classes", response_model=list[ClassResponse])
async def get_classes_by_teacher(
    teacher_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_teacher_access(teacher_id, session, current_user)
    result = await session.execute(
        select(Class)
        .join(TeacherSubject, TeacherSubject.class_id == Class.id)
        .where(TeacherSubject.teacher_id == teacher_id)
        .distinct()
    )
    return result.scalars().all()


@router.get("/{teacher_id}/subjects", response_model=list[SubjectResponse])
async def get_subjects_by_teacher(
    teacher_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_teacher_access(teacher_id, session, current_user)
    result = await session.execute(
        select(Subject)
        .join(TeacherSubject, TeacherSubject.subject_id == Subject.id)
        .where(TeacherSubject.teacher_id == teacher_id)
        .distinct()
    )
    return result.scalars().all()


@router.get("/me", response_model=TeacherResponse)
async def get_current_teacher(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(
        select(Teacher).where(Teacher.user_id == current_user.id)
    )
    teacher = result.scalar_one_or_none()
    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found",
        )
    return teacher


@router.get("/{teacher_id}/timetable")
async def get_teacher_timetable(
    teacher_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_teacher_access(teacher_id, session, current_user)
    result = await session.execute(
        select(Timetable)
        .where(Timetable.teacher_id == teacher_id)
        .order_by(Timetable.day_of_week, Timetable.start_time)
    )
    timetables = result.scalars().all()
    return [
        {
            "id": str(t.id),
            "class_id": str(t.class_id),
            "subject_id": str(t.subject_id),
            "day_of_week": t.day_of_week,
            "start_time": t.start_time.strftime("%H:%M"),
            "end_time": t.end_time.strftime("%H:%M"),
            "room_no": t.room_no,
            "class_name": t.class_.class_name if t.class_ else None,
            "subject_name": t.subject.subject_name if t.subject else None,
        }
        for t in timetables
    ]


@router.get("/{teacher_id}/pending-submissions")
async def get_teacher_pending_submissions(
    teacher_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_teacher_access(teacher_id, session, current_user)
    from app.models.assignment_model import AssignmentSubmission, Assignment
    result = await session.execute(
        select(AssignmentSubmission, Assignment, Class, Student, Subject)
        .join(Assignment, Assignment.id == AssignmentSubmission.assignment_id)
        .join(Class, Class.id == Assignment.class_id)
        .join(Student, Student.id == AssignmentSubmission.student_id)
        .join(Subject, Subject.id == Assignment.subject_id)
        .where(Assignment.teacher_id == teacher_id)
        .where(AssignmentSubmission.marks.is_(None))
        .order_by(AssignmentSubmission.submitted_on.desc())
    )
    rows = result.all()
    return [
        {
            "id": str(sub.id),
            "assignment_id": str(assignment.id),
            "assignment_title": assignment.title,
            "class_name": cls.class_name,
            "subject_name": subject.subject_name,
            "student_name": f"{student.first_name or ''} {student.last_name or ''}".strip() or student.admission_no,
            "submitted_on": str(sub.submitted_on),
            "file_path": sub.file_path,
        }
        for sub, assignment, cls, student, subject in rows
    ]


@router.get("/{teacher_id}/performance")
async def get_teacher_performance(
    teacher_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_teacher_access(teacher_id, session, current_user)
    result = await session.execute(
        select(Class.id, Class.class_name, func.avg(ExamResult.marks_obtained).label("avg_marks"))
        .join(Timetable, Timetable.class_id == Class.id)
        .join(Exam, Exam.class_id == Class.id)
        .join(ExamResult, ExamResult.exam_id == Exam.id)
        .where(Timetable.teacher_id == teacher_id)
        .group_by(Class.id, Class.class_name)
    )
    rows = result.all()
    return [
        {
            "class_id": str(row.id),
            "class_name": row.class_name,
            "average_marks": round(float(row.avg_marks), 2) if row.avg_marks else 0,
        }
        for row in rows
    ]

@router.get("/{teacher_id}/messages")
async def get_teacher_messages(
    teacher_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_teacher_access(teacher_id, session, current_user)
    teacher = await session.execute(select(Teacher).where(Teacher.id == teacher_id))
    teacher_obj = teacher.scalar_one_or_none()
    if not teacher_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")

    result = await session.execute(
        select(Message, User)
        .join(User, User.id == Message.sender_id)
        .where(Message.receiver_id == teacher_obj.user_id)
        .order_by(Message.sent_on.desc())
        .limit(10)
    )
    rows = result.all()
    return [
        {
            "id": str(msg.id),
            "sender_name": user.username,
            "message": msg.message,
            "sent_on": str(msg.sent_on),
            "is_read": msg.is_read,
        }
        for msg, user in rows
    ]


@router.get("/{teacher_id}/events")
async def get_teacher_events(
    teacher_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_teacher_access(teacher_id, session, current_user)
    from app.models.event_model import Event
    result = await session.execute(
        select(Event)
        .where(Event.start_date >= func.current_date())
        .order_by(Event.start_date.asc())
        .limit(10)
    )
    events = result.scalars().all()
    return [
        {
            "id": str(event.id),
            "event_name": event.event_name,
            "description": event.description,
            "start_date": str(event.start_date),
            "end_date": str(event.end_date) if event.end_date else None,
        }
        for event in events
    ]


@router.get("/{teacher_id}/assignments")
async def get_teacher_assignments(
    teacher_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_teacher_access(teacher_id, session, current_user)
    result = await session.execute(
        select(Assignment, Class, Subject)
        .join(Class, Class.id == Assignment.class_id)
        .join(Subject, Subject.id == Assignment.subject_id)
        .where(Assignment.teacher_id == teacher_id)
        .order_by(Assignment.created_at.desc())
    )
    rows = result.all()
    return [
        {
            "id": str(assignment.id),
            "title": assignment.title,
            "description": assignment.description,
            "due_date": str(assignment.due_date),
            "class_name": cls.class_name,
            "subject_name": subject.subject_name,
            "created_at": str(assignment.created_at),
        }
        for assignment, cls, subject in rows
    ]


@router.get("/{teacher_id}/exam-results")
async def get_teacher_exam_results(
    teacher_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_teacher_access(teacher_id, session, current_user)
    result = await session.execute(
        select(ExamResult, Exam, Class, Subject, Student)
        .join(Exam, Exam.id == ExamResult.exam_id)
        .join(Class, Class.id == Exam.class_id)
        .join(Subject, Subject.id == ExamResult.subject_id)
        .join(Student, Student.id == ExamResult.student_id)
        .join(
            TeacherSubject,
            (TeacherSubject.class_id == Exam.class_id)
            & (TeacherSubject.subject_id == ExamResult.subject_id),
        )
        .where(TeacherSubject.teacher_id == teacher_id)
        .order_by(ExamResult.created_at.desc())
        .limit(50)
    )
    rows = result.all()
    return [
        {
            "id": str(result.id),
            "student_name": f"{student.first_name or ''} {student.last_name or ''}".strip() or student.admission_no,
            "class_name": cls.class_name,
            "subject_name": subject.subject_name,
            "exam_name": exam.exam_name,
            "marks_obtained": float(result.marks_obtained) if result.marks_obtained else 0,
            "max_marks": float(exam.max_marks) if exam.max_marks else 100,
            "grade": result.grade,
            "created_at": str(result.created_at),
        }
        for result, exam, cls, subject, student in rows
    ]
