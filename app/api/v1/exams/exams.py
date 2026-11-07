from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.models.exam_model import Exam
from app.models.user import User
from app.schemas.exam_schema import ExamCreate, ExamResponse, ExamTopperResponse, ExamUpdate
from app.services.exam_service import exam_service
from app.services.report_card_service import report_card_service

router = APIRouter()


def _ensure_admin_or_teacher(current_user: User) -> None:
    role_name = (current_user.role.role_name if current_user.role else "").upper()
    if role_name not in ("ADMIN", "SUPER_ADMIN", "TEACHER"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or teacher users can perform this action",
        )


def _ensure_can_read_exams(current_user: User) -> None:
    role_name = (current_user.role.role_name if current_user.role else "").upper()
    if role_name not in ("ADMIN", "SUPER_ADMIN", "TEACHER", "STUDENT", "PARENT"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view examinations",
        )


@router.get("", response_model=list[ExamResponse])
async def list_exams(
    class_id: UUID | None = None,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_can_read_exams(current_user)
    if class_id:
        result = await session.execute(
            select(Exam).where(Exam.class_id == class_id)
        )
        return result.scalars().all()
    res = await exam_service.list(session)
    return res["items"] if isinstance(res, dict) and "items" in res else res


@router.get("/{item_id}", response_model=ExamResponse)
async def get_exam(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_can_read_exams(current_user)
    return await exam_service.get(session, item_id)


@router.post("", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
async def create_exam(
    payload: ExamCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_teacher(current_user)
    return await exam_service.create(session, payload.model_dump())


@router.put("/{item_id}", response_model=ExamResponse)
async def update_exam(
    item_id: UUID,
    payload: ExamUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_teacher(current_user)
    return await exam_service.update(session, item_id, payload.model_dump(exclude_unset=True))


@router.delete("/{item_id}")
async def delete_exam(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_teacher(current_user)
    await exam_service.delete(session, item_id)
    return {"message": "Deleted successfully"}


@router.get("/{exam_id}/toppers", response_model=list[ExamTopperResponse])
async def get_exam_toppers(
    exam_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_can_read_exams(current_user)
    return await report_card_service.get_toppers(session, exam_id)
