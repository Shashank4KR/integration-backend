from uuid import UUID

from fastapi import Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.api.v1.router_factory import build_crud_router
from app.core.database import get_db
from app.models.exam_result_model import ExamResult
from app.models.user import User
from app.schemas.exam_schema import ExamResultResponse
from app.schemas.subject_schema import SubjectCreate, SubjectResponse, SubjectUpdate
from app.services.subject_service import subject_service

router = build_crud_router(subject_service, SubjectCreate, SubjectUpdate, SubjectResponse)


def _ensure_admin_or_teacher(current_user: User) -> None:
    if current_user.role.role_name not in ("ADMIN", "TEACHER"):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or teacher users can perform this action",
        )


@router.post("", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(
    payload: SubjectCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_teacher(current_user)
    return await subject_service.create(session, payload.model_dump())


@router.put("/{item_id}", response_model=SubjectResponse)
async def update_subject(
    item_id: UUID,
    payload: SubjectUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_teacher(current_user)
    return await subject_service.update(session, item_id, payload.model_dump(exclude_unset=True))


@router.delete("/{item_id}")
async def delete_subject(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_teacher(current_user)
    await subject_service.delete(session, item_id)
    return {"message": "Deleted successfully"}


@router.get("/{subject_id}/exam-results", response_model=list[ExamResultResponse])
async def get_subject_exam_results(
    subject_id: UUID, session: AsyncSession = Depends(get_db)
):
    await subject_service.get(session, subject_id)
    result = await session.execute(
        select(ExamResult).where(ExamResult.subject_id == subject_id)
    )
    return result.scalars().all()
