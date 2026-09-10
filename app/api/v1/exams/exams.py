from uuid import UUID

from fastapi import Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.api.v1.router_factory import build_crud_router
from app.core.database import get_db
from app.models.user import User
from app.schemas.exam_schema import ExamCreate, ExamResponse, ExamTopperResponse, ExamUpdate
from app.services.exam_service import exam_service
from app.services.report_card_service import report_card_service

router = build_crud_router(exam_service, ExamCreate, ExamUpdate, ExamResponse)


def _ensure_admin_or_teacher(current_user: User) -> None:
    if current_user.role.role_name not in ("ADMIN", "TEACHER"):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or teacher users can perform this action",
        )


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
async def get_exam_toppers(exam_id: UUID, session: AsyncSession = Depends(get_db)):
    return await report_card_service.get_toppers(session, exam_id)
