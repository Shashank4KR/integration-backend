from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.assignment_schema import AssignmentCreate, AssignmentResponse, AssignmentSubmissionCreate, AssignmentSubmissionResponse, AssignmentSubmissionUpdate, AssignmentSummaryResponse, AssignmentUpdate
from app.services.assignment_service import assignment_service, submission_service

router = APIRouter()


def _ensure_admin_or_teacher(current_user: User) -> None:
    role_name = (current_user.role.role_name if current_user.role else "").upper()
    if role_name not in ("ADMIN", "TEACHER"):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or teacher users can perform this action",
        )


@router.post("", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(payload: AssignmentCreate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_teacher(current_user)
    return await assignment_service.create_assignment(session, payload.model_dump())

@router.get("", response_model=list[AssignmentResponse])
async def get_assignments(session: AsyncSession = Depends(get_db)): return await assignment_service.get_assignments(session)

@router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(assignment_id: UUID, session: AsyncSession = Depends(get_db)): return await assignment_service.get_assignment(session, assignment_id)

@router.put("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(assignment_id: UUID, payload: AssignmentUpdate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_teacher(current_user)
    return await assignment_service.update_assignment(session, assignment_id, payload.model_dump(exclude_unset=True))

@router.delete("/{assignment_id}")
async def delete_assignment(assignment_id: UUID, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_teacher(current_user)
    await assignment_service.delete_assignment(session, assignment_id)
    return {"message": "Deleted successfully"}

@router.get("/{assignment_id}/submissions", response_model=list[AssignmentSubmissionResponse])
async def assignment_submissions(assignment_id: UUID, session: AsyncSession = Depends(get_db)): return await submission_service.repository.get_by_assignment(session, assignment_id)

@router.get("/{assignment_id}/summary", response_model=AssignmentSummaryResponse)
async def assignment_summary(assignment_id: UUID, session: AsyncSession = Depends(get_db)): return await assignment_service.summary(session, assignment_id)

submission_router = APIRouter()


@submission_router.post("", response_model=AssignmentSubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_assignment(payload: AssignmentSubmissionCreate, session: AsyncSession = Depends(get_db)):
    return await submission_service.submit_assignment(session, payload.model_dump(exclude_none=True))

@submission_router.get("", response_model=list[AssignmentSubmissionResponse])
async def get_submissions(session: AsyncSession = Depends(get_db)): return await submission_service.get_submissions(session)

@submission_router.get("/{submission_id}", response_model=AssignmentSubmissionResponse)
async def get_submission(submission_id: UUID, session: AsyncSession = Depends(get_db)): return await submission_service.get_submission(session, submission_id)

@submission_router.put("/{submission_id}", response_model=AssignmentSubmissionResponse)
async def update_submission(submission_id: UUID, payload: AssignmentSubmissionUpdate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_teacher(current_user)
    return await submission_service.update_submission(session, submission_id, payload.model_dump(exclude_unset=True))

@submission_router.delete("/{submission_id}")
async def delete_submission(submission_id: UUID, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_teacher(current_user)
    await submission_service.delete_submission(session, submission_id)
    return {"message": "Deleted successfully"}

teacher_assignment_router = APIRouter()
@teacher_assignment_router.get("/{teacher_id}/assignments", response_model=list[AssignmentResponse])
async def teacher_assignments(teacher_id: UUID, session: AsyncSession = Depends(get_db)): return await assignment_service.repository.get_by_teacher(session, teacher_id)

class_assignment_router = APIRouter()
@class_assignment_router.get("/{class_id}/assignments", response_model=list[AssignmentResponse])
async def class_assignments(class_id: UUID, session: AsyncSession = Depends(get_db)): return await assignment_service.repository.get_by_class(session, class_id)

student_assignment_router = APIRouter()
@student_assignment_router.get("/{student_id}/assignments", response_model=list[AssignmentResponse])
async def student_assignments(student_id: UUID, session: AsyncSession = Depends(get_db)):
    from app.models.student_model import Student
    student = await session.get(Student, student_id)
    if student is None: from fastapi import HTTPException; raise HTTPException(status_code=404, detail="Student not found")
    return await assignment_service.repository.get_by_class(session, student.class_id)

@student_assignment_router.get("/{student_id}/submissions", response_model=list[AssignmentSubmissionResponse])
async def student_submissions(student_id: UUID, session: AsyncSession = Depends(get_db)): return await submission_service.repository.get_by_student(session, student_id)
