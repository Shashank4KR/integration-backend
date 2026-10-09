import logging
import os
import uuid
from datetime import date
from typing import List, Optional
from uuid import UUID

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.models.academic_content_model import ChapterNote, ContentResource, LessonPlan, StudentFeedback
from app.models.class_model import Class
from app.models.parent_model import Parent
from app.models.parent_student_model import ParentStudent
from app.models.student_model import Student
from app.models.subject_model import Subject
from app.models.teacher_model import Teacher
from app.models.teacher_subject_model import TeacherSubject
from app.models.user import User
from app.schemas.academic_content_schema import (
    ChapterNoteResponse,
    ContentResourceCreate,
    ContentResourceResponse,
    ContentResourceUpdate,
    LessonPlanCreate,
    LessonPlanResponse,
    LessonPlanUpdate,
    StudentFeedbackCreate,
    StudentFeedbackResponse,
    StudentFeedbackUpdate,
)

router = APIRouter()

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads", "notes")
os.makedirs(UPLOAD_DIR, exist_ok=True)
MAX_NOTE_SIZE = 10 * 1024 * 1024


async def _accessible_class_ids(session: AsyncSession, user: User) -> set[UUID] | None:
    """Return allowed class IDs, None for an administrator, and an empty set for no access."""
    role_name = (user.role.role_name if user.role else "").upper()
    if role_name == "ADMIN":
        return None
    if role_name == "STUDENT":
        result = await session.execute(select(Student.class_id).where(Student.user_id == user.id))
        class_id = result.scalar_one_or_none()
        return {class_id} if class_id else set()
    if role_name == "PARENT":
        result = await session.execute(
            select(Student.class_id)
            .join(ParentStudent, ParentStudent.student_id == Student.id)
            .join(Parent, Parent.id == ParentStudent.parent_id)
            .where(Parent.user_id == user.id, Student.class_id.is_not(None))
        )
        return set(result.scalars().all())
    if role_name == "TEACHER":
        teacher_result = await session.execute(select(Teacher.id).where(Teacher.user_id == user.id))
        teacher_id = teacher_result.scalar_one_or_none()
        if not teacher_id:
            return set()
        assigned = await session.execute(
            select(TeacherSubject.class_id).where(TeacherSubject.teacher_id == teacher_id)
        )
        class_teacher = await session.execute(
            select(Class.id).where(Class.class_teacher_id == teacher_id)
        )
        return set(assigned.scalars().all()) | set(class_teacher.scalars().all())
    return set()


async def _require_class_access(
    session: AsyncSession, user: User, class_id: UUID, *, teacher_id: UUID | None = None
) -> UUID | None:
    allowed = await _accessible_class_ids(session, user)
    if allowed is not None and class_id not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied for this class")
    if (user.role.role_name if user.role else "").upper() == "TEACHER" and teacher_id is not None:
        teacher = await session.execute(select(Teacher.id).where(Teacher.user_id == user.id))
        if teacher.scalar_one_or_none() != teacher_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied for this teacher's record")
    return allowed


async def _get_teacher_for_user(session: AsyncSession, user: User) -> Teacher:
    role_name = user.role.role_name.upper() if user.role else ""
    if role_name != "TEACHER" and role_name != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not authorized as a teacher",
        )
    result = await session.execute(select(Teacher).where(Teacher.user_id == user.id))
    teacher = result.scalar_one_or_none()
    if not teacher and role_name != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found",
        )
    return teacher


async def _ensure_teacher_assigned(
    session: AsyncSession,
    user: User,
    class_id: UUID,
    subject_id: UUID,
) -> Teacher:
    role_name = user.role.role_name.upper() if user.role else ""
    if role_name == "ADMIN":
        result = await session.execute(select(Teacher).where(Teacher.user_id == user.id))
        teacher = result.scalar_one_or_none()
        if teacher:
            return teacher
        res = await session.execute(select(Teacher).limit(1))
        teacher = res.scalar_one_or_none()
        if teacher:
            return teacher
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No teacher profile exists in the database.",
        )


    teacher = await _get_teacher_for_user(session, user)
    res = await session.execute(
        select(TeacherSubject).where(
            TeacherSubject.teacher_id == teacher.id,
            TeacherSubject.class_id == class_id,
            TeacherSubject.subject_id == subject_id,
        )
    )
    if res.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher is not assigned to this grade/class and subject",
        )
    return teacher


# ==================== LESSON PLANS ====================

@router.post("/lesson-plans", response_model=LessonPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_lesson_plan(
    payload: LessonPlanCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    teacher = await _ensure_teacher_assigned(
        session, current_user, payload.class_id, payload.subject_id
    )
    plan = LessonPlan(
        teacher_id=teacher.id,
        class_id=payload.class_id,
        subject_id=payload.subject_id,
        chapter_name=payload.chapter_name,
        topic=payload.topic,
        plan_date=payload.plan_date,
        objectives=payload.objectives,
        materials_needed=payload.materials_needed,
        procedure_summary=payload.procedure_summary,
        homework_notes=payload.homework_notes,
        status=payload.status,
    )
    session.add(plan)
    await session.commit()
    await session.refresh(plan)

    cls = await session.get(Class, plan.class_id)
    subj = await session.get(Subject, plan.subject_id)
    return LessonPlanResponse(
        id=plan.id,
        teacher_id=plan.teacher_id,
        class_id=plan.class_id,
        subject_id=plan.subject_id,
        chapter_name=plan.chapter_name,
        topic=plan.topic,
        plan_date=plan.plan_date,
        objectives=plan.objectives,
        materials_needed=plan.materials_needed,
        procedure_summary=plan.procedure_summary,
        homework_notes=plan.homework_notes,
        status=plan.status,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
        class_name=cls.class_name if cls else None,
        subject_name=subj.subject_name if subj else None,
    )


@router.get("/lesson-plans", response_model=List[LessonPlanResponse])
async def get_lesson_plans(
    class_id: Optional[UUID] = Query(None),
    subject_id: Optional[UUID] = Query(None),
    chapter_name: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(LessonPlan, Class, Subject, Teacher).join(Class, Class.id == LessonPlan.class_id).join(Subject, Subject.id == LessonPlan.subject_id).join(Teacher, Teacher.id == LessonPlan.teacher_id)
    
    role_name = current_user.role.role_name.upper() if current_user.role else ""
    allowed_classes = await _accessible_class_ids(session, current_user)
    if role_name not in {"ADMIN", "TEACHER", "STUDENT", "PARENT"}:
        raise HTTPException(status_code=403, detail="Access denied")
    if allowed_classes is not None:
        if class_id is not None and class_id not in allowed_classes:
            raise HTTPException(status_code=403, detail="Access denied for this class")
        stmt = stmt.where(LessonPlan.class_id.in_(allowed_classes))
    if role_name == "TEACHER":
        teacher_result = await session.execute(select(Teacher.id).where(Teacher.user_id == current_user.id))
        teacher_id = teacher_result.scalar_one_or_none()
        if not teacher_id:
            raise HTTPException(status_code=403, detail="Teacher profile not found")
        stmt = stmt.where(LessonPlan.teacher_id == teacher_id)
            
    if class_id:
        stmt = stmt.where(LessonPlan.class_id == class_id)
    if subject_id:
        stmt = stmt.where(LessonPlan.subject_id == subject_id)
    if chapter_name:
        stmt = stmt.where(LessonPlan.chapter_name.ilike(f"%{chapter_name}%"))

    stmt = stmt.order_by(LessonPlan.plan_date.desc())
    res = await session.execute(stmt)
    rows = res.all()
    return [
        LessonPlanResponse(
            id=plan.id,
            teacher_id=plan.teacher_id,
            class_id=plan.class_id,
            subject_id=plan.subject_id,
            chapter_name=plan.chapter_name,
            topic=plan.topic,
            plan_date=plan.plan_date,
            objectives=plan.objectives,
            materials_needed=plan.materials_needed,
            procedure_summary=plan.procedure_summary,
            homework_notes=plan.homework_notes,
            status=plan.status,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
            class_name=cls.class_name,
            subject_name=subj.subject_name,
            teacher_name=teacher.employee_id,
        )
        for plan, cls, subj, teacher in rows
    ]


@router.put("/lesson-plans/{plan_id}", response_model=LessonPlanResponse)
async def update_lesson_plan(
    plan_id: UUID,
    payload: LessonPlanUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = await session.get(LessonPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson plan not found")

    role_name = (current_user.role.role_name if current_user.role else "").upper()
    if role_name not in {"ADMIN", "TEACHER"}:
        raise HTTPException(status_code=403, detail="Only an assigned teacher or administrator may update lesson plans")
    await _require_class_access(session, current_user, plan.class_id, teacher_id=plan.teacher_id)
    updates = payload.model_dump(exclude_unset=True)
    target_class = updates.get("class_id", plan.class_id)
    target_subject = updates.get("subject_id", plan.subject_id)
    if role_name == "TEACHER":
        teacher = await _ensure_teacher_assigned(session, current_user, target_class, target_subject)
    else:
        teacher = None
    if role_name == "TEACHER" and teacher.id != plan.teacher_id:
        raise HTTPException(status_code=403, detail="Only the owning teacher may update this lesson plan")
    for k, v in updates.items():
        setattr(plan, k, v)
    await session.commit()
    await session.refresh(plan)

    cls = await session.get(Class, plan.class_id)
    subj = await session.get(Subject, plan.subject_id)
    return LessonPlanResponse(
        id=plan.id,
        teacher_id=plan.teacher_id,
        class_id=plan.class_id,
        subject_id=plan.subject_id,
        chapter_name=plan.chapter_name,
        topic=plan.topic,
        plan_date=plan.plan_date,
        objectives=plan.objectives,
        materials_needed=plan.materials_needed,
        procedure_summary=plan.procedure_summary,
        homework_notes=plan.homework_notes,
        status=plan.status,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
        class_name=cls.class_name if cls else None,
        subject_name=subj.subject_name if subj else None,
    )


@router.delete("/lesson-plans/{plan_id}")
async def delete_lesson_plan(
    plan_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = await session.get(LessonPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson plan not found")
    role_name = (current_user.role.role_name if current_user.role else "").upper()
    if role_name not in {"ADMIN", "TEACHER"}:
        raise HTTPException(status_code=403, detail="Only an assigned teacher or administrator may delete lesson plans")
    await _require_class_access(session, current_user, plan.class_id, teacher_id=plan.teacher_id)
    await session.delete(plan)
    await session.commit()
    return {"message": "Lesson plan deleted successfully"}


# ==================== CONTENT RESOURCES ====================

@router.post("/content-resources", response_model=ContentResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_content_resource(
    payload: ContentResourceCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    teacher = await _ensure_teacher_assigned(
        session, current_user, payload.class_id, payload.subject_id
    )
    resource = ContentResource(
        teacher_id=teacher.id,
        class_id=payload.class_id,
        subject_id=payload.subject_id,
        chapter_name=payload.chapter_name,
        title=payload.title,
        url=payload.url,
        description=payload.description,
    )
    session.add(resource)
    await session.commit()
    await session.refresh(resource)

    cls = await session.get(Class, resource.class_id)
    subj = await session.get(Subject, resource.subject_id)
    return ContentResourceResponse(
        id=resource.id,
        teacher_id=resource.teacher_id,
        class_id=resource.class_id,
        subject_id=resource.subject_id,
        chapter_name=resource.chapter_name,
        title=resource.title,
        url=resource.url,
        description=resource.description,
        created_at=resource.created_at,
        updated_at=resource.updated_at,
        class_name=cls.class_name if cls else None,
        subject_name=subj.subject_name if subj else None,
    )


@router.get("/content-resources", response_model=List[ContentResourceResponse])
async def get_content_resources(
    class_id: Optional[UUID] = Query(None),
    subject_id: Optional[UUID] = Query(None),
    chapter_name: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(ContentResource, Class, Subject).join(Class, Class.id == ContentResource.class_id).join(Subject, Subject.id == ContentResource.subject_id)
    
    role_name = current_user.role.role_name.upper() if current_user.role else ""
    if role_name == "STUDENT":
        student_res = await session.execute(select(Student).where(Student.user_id == current_user.id))
        student = student_res.scalar_one_or_none()
        if student and student.class_id:
            stmt = stmt.where(ContentResource.class_id == student.class_id)
            
    if class_id:
        stmt = stmt.where(ContentResource.class_id == class_id)
    if subject_id:
        stmt = stmt.where(ContentResource.subject_id == subject_id)
    if chapter_name:
        stmt = stmt.where(ContentResource.chapter_name.ilike(f"%{chapter_name}%"))

    stmt = stmt.order_by(ContentResource.created_at.desc())
    res = await session.execute(stmt)
    rows = res.all()
    return [
        ContentResourceResponse(
            id=item.id,
            teacher_id=item.teacher_id,
            class_id=item.class_id,
            subject_id=item.subject_id,
            chapter_name=item.chapter_name,
            title=item.title,
            url=item.url,
            description=item.description,
            created_at=item.created_at,
            updated_at=item.updated_at,
            class_name=cls.class_name,
            subject_name=subj.subject_name,
        )
        for item, cls, subj in rows
    ]


@router.delete("/content-resources/{resource_id}")
async def delete_content_resource(
    resource_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = await session.get(ContentResource, resource_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    await session.delete(item)
    await session.commit()
    return {"message": "Content resource deleted successfully"}


# ==================== CHAPTER NOTES ====================

@router.post("/chapter-notes/upload", response_model=ChapterNoteResponse, status_code=status.HTTP_201_CREATED)
async def upload_chapter_note(
    class_id: UUID = Form(...),
    subject_id: UUID = Form(...),
    chapter_name: str = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
    request: Request = None,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    teacher = await _ensure_teacher_assigned(session, current_user, class_id, subject_id)
    content_length = request.headers.get("content-length") if request else None
    if content_length and int(content_length) > MAX_NOTE_SIZE + 1024 * 1024:
        raise HTTPException(status_code=413, detail="Upload exceeds the 10 MB limit")
    allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg"}
    extension = os.path.splitext(file.filename or "")[1].lower()
    if extension not in allowed_extensions:
        raise HTTPException(status_code=415, detail="Only PDF, PNG, and JPEG files are allowed")

    temp_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.upload")
    size = 0
    signature = b""
    try:
        with open(temp_path, "wb") as destination:
            while chunk := await file.read(64 * 1024):
                size += len(chunk)
                if size > MAX_NOTE_SIZE:
                    raise HTTPException(status_code=413, detail="Upload exceeds the 10 MB limit")
                if len(signature) < 16:
                    signature += chunk[: 16 - len(signature)]
                destination.write(chunk)
        if extension == ".pdf" and signature.startswith(b"%PDF-"):
            safe_extension, detected_type = ".pdf", "application/pdf"
        elif extension == ".png" and signature.startswith(b"\x89PNG\r\n\x1a\n"):
            safe_extension, detected_type = ".png", "image/png"
        elif extension in {".jpg", ".jpeg"} and signature.startswith(b"\xff\xd8\xff"):
            safe_extension, detected_type = ".jpg", "image/jpeg"
        else:
            raise HTTPException(status_code=415, detail="File content does not match an allowed file type")
        stored_filename = f"{uuid.uuid4()}{safe_extension}"
        file_path = os.path.join(UPLOAD_DIR, stored_filename)
        os.replace(temp_path, file_path)
    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise

    file_url = f"/api/chapter-notes/files/{stored_filename}"

    note = ChapterNote(
        teacher_id=teacher.id,
        class_id=class_id,
        subject_id=subject_id,
        chapter_name=chapter_name,
        title=title,
        file_url=file_url,
        file_name=file.filename or stored_filename,
        file_size=size,
        mime_type=detected_type,
    )
    session.add(note)
    await session.commit()
    await session.refresh(note)

    cls = await session.get(Class, note.class_id)
    subj = await session.get(Subject, note.subject_id)
    return ChapterNoteResponse(
        id=note.id,
        teacher_id=note.teacher_id,
        class_id=note.class_id,
        subject_id=note.subject_id,
        chapter_name=note.chapter_name,
        title=note.title,
        file_url=note.file_url,
        file_name=note.file_name,
        file_size=note.file_size,
        mime_type=note.mime_type,
        created_at=note.created_at,
        updated_at=note.updated_at,
        class_name=cls.class_name if cls else None,
        subject_name=subj.subject_name if subj else None,
    )


@router.get("/chapter-notes/files/{filename}")
async def download_chapter_note_file(
    filename: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if os.path.basename(filename) != filename or filename in {"", ".", ".."}:
        raise HTTPException(status_code=404, detail="File not found")
    note_result = await session.execute(
        select(ChapterNote).where(ChapterNote.file_url == f"/api/chapter-notes/files/{filename}")
    )
    note = note_result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="File not found")
    await _require_class_access(session, current_user, note.class_id)
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=os.path.basename(filename),
        content_disposition_type="attachment",
        headers={"X-Content-Type-Options": "nosniff", "Content-Security-Policy": "sandbox"},
    )


@router.get("/chapter-notes", response_model=List[ChapterNoteResponse])
async def get_chapter_notes(
    class_id: Optional[UUID] = Query(None),
    subject_id: Optional[UUID] = Query(None),
    chapter_name: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(ChapterNote, Class, Subject).join(Class, Class.id == ChapterNote.class_id).join(Subject, Subject.id == ChapterNote.subject_id)

    role_name = current_user.role.role_name.upper() if current_user.role else ""
    allowed_classes = await _accessible_class_ids(session, current_user)
    if role_name not in {"ADMIN", "TEACHER", "STUDENT", "PARENT"}:
        raise HTTPException(status_code=403, detail="Access denied")
    if allowed_classes is not None:
        if class_id is not None and class_id not in allowed_classes:
            raise HTTPException(status_code=403, detail="Access denied for this class")
        stmt = stmt.where(ChapterNote.class_id.in_(allowed_classes))
    if role_name == "TEACHER":
        teacher_result = await session.execute(select(Teacher.id).where(Teacher.user_id == current_user.id))
        teacher_id = teacher_result.scalar_one_or_none()
        if not teacher_id:
            raise HTTPException(status_code=403, detail="Teacher profile not found")
        stmt = stmt.where(ChapterNote.teacher_id == teacher_id)

    if class_id:
        stmt = stmt.where(ChapterNote.class_id == class_id)
    if subject_id:
        stmt = stmt.where(ChapterNote.subject_id == subject_id)
    if chapter_name:
        stmt = stmt.where(ChapterNote.chapter_name.ilike(f"%{chapter_name}%"))

    stmt = stmt.order_by(ChapterNote.created_at.desc())
    res = await session.execute(stmt)
    rows = res.all()
    return [
        ChapterNoteResponse(
            id=note.id,
            teacher_id=note.teacher_id,
            class_id=note.class_id,
            subject_id=note.subject_id,
            chapter_name=note.chapter_name,
            title=note.title,
            file_url=note.file_url,
            file_name=note.file_name,
            file_size=note.file_size,
            mime_type=note.mime_type,
            created_at=note.created_at,
            updated_at=note.updated_at,
            class_name=cls.class_name,
            subject_name=subj.subject_name,
        )
        for note, cls, subj in rows
    ]


@router.delete("/chapter-notes/{note_id}")
async def delete_chapter_note(
    note_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = await session.get(ChapterNote, note_id)
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter note not found")

    role_name = (current_user.role.role_name if current_user.role else "").upper()
    if role_name not in {"ADMIN", "TEACHER"}:
        raise HTTPException(status_code=403, detail="Only an assigned teacher or administrator may delete notes")
    await _require_class_access(session, current_user, note.class_id, teacher_id=note.teacher_id)

    # If file exists on disk, remove it
    if note.file_url:
        filename = os.path.basename(note.file_url)
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"Failed to remove note file {file_path}: {e}")

    await session.delete(note)
    await session.commit()
    return {"message": "Chapter note deleted successfully"}


# ==================== STUDENT FEEDBACK ====================

@router.post("/student-feedback", response_model=StudentFeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_student_feedback(
    payload: StudentFeedbackCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    teacher = await _get_teacher_for_user(session, current_user)
    feedback = StudentFeedback(
        teacher_id=teacher.id,
        student_id=payload.student_id,
        feedback_type=payload.feedback_type,
        comment=payload.comment,
        feedback_date=payload.feedback_date,
    )
    session.add(feedback)
    await session.commit()
    await session.refresh(feedback)

    student = await session.get(Student, feedback.student_id)
    student_name = f"{student.first_name or ''} {student.last_name or ''}".strip() if student else None
    return StudentFeedbackResponse(
        id=feedback.id,
        teacher_id=feedback.teacher_id,
        student_id=feedback.student_id,
        feedback_type=feedback.feedback_type,
        comment=feedback.comment,
        feedback_date=feedback.feedback_date,
        created_at=feedback.created_at,
        updated_at=feedback.updated_at,
        teacher_name=teacher.employee_id,
        student_name=student_name,
    )


@router.get("/student-feedback", response_model=List[StudentFeedbackResponse])
async def get_student_feedback(
    student_id: Optional[UUID] = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(StudentFeedback, Student, Teacher).join(Student, Student.id == StudentFeedback.student_id).join(Teacher, Teacher.id == StudentFeedback.teacher_id)

    role_name = current_user.role.role_name.upper() if current_user.role else ""
    if role_name == "STUDENT":
        s_res = await session.execute(select(Student).where(Student.user_id == current_user.id))
        s_obj = s_res.scalar_one_or_none()
        if s_obj:
            stmt = stmt.where(StudentFeedback.student_id == s_obj.id)
    elif role_name == "PARENT":
        p_res = await session.execute(
            select(ParentStudent.student_id)
            .join(Parent, Parent.id == ParentStudent.parent_id)
            .where(Parent.user_id == current_user.id)
        )
        linked_student_ids = p_res.scalars().all()
        if not linked_student_ids:
            return []
        stmt = stmt.where(StudentFeedback.student_id.in_(linked_student_ids))


    if student_id:
        stmt = stmt.where(StudentFeedback.student_id == student_id)

    stmt = stmt.order_by(StudentFeedback.created_at.desc())
    res = await session.execute(stmt)
    rows = res.all()
    return [
        StudentFeedbackResponse(
            id=fb.id,
            teacher_id=fb.teacher_id,
            student_id=fb.student_id,
            feedback_type=fb.feedback_type,
            comment=fb.comment,
            feedback_date=fb.feedback_date,
            created_at=fb.created_at,
            updated_at=fb.updated_at,
            teacher_name=teacher.employee_id,
            student_name=f"{student.first_name or ''} {student.last_name or ''}".strip(),
        )
        for fb, student, teacher in rows
    ]


@router.delete("/student-feedback/{feedback_id}")
async def delete_student_feedback(
    feedback_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    fb = await session.get(StudentFeedback, feedback_id)
    if not fb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")
    await session.delete(fb)
    await session.commit()
    return {"message": "Feedback deleted successfully"}
