from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.exam_schema import ReportCardGenerate, ReportCardResponse
from app.services.report_card_service import report_card_service

router = APIRouter()


def _ensure_admin_or_teacher(current_user: User) -> None:
    if current_user.role.role_name not in ("ADMIN", "TEACHER"):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or teacher users can perform this action",
        )


@router.post("/generate", response_model=ReportCardResponse)
async def generate_report_card(
    payload: ReportCardGenerate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_teacher(current_user)
    return await report_card_service.generate_report_card(
        session, payload.student_id, payload.exam_id, payload.remarks
    )


@router.post("/publish/{exam_id}", status_code=status.HTTP_200_OK)
async def publish_exam_results(
    exam_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_teacher(current_user)
    from fastapi import HTTPException
    from sqlalchemy import select
    from app.models.exam_model import Exam
    from app.models.student_model import Student

    exam = await session.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    result = await session.execute(
        select(Student).where(Student.class_id == exam.class_id)
    )
    students = result.scalars().all()
    if not students:
        raise HTTPException(status_code=400, detail="No students found in this exam's class")

    generated = 0
    for student in students:
        try:
            await report_card_service.generate_report_card(
                session, student.id, exam_id, remarks="Published exam result"
            )
            generated += 1
        except Exception:
            pass

    return {"message": f"Successfully published results. Generated {generated} report cards."}


@router.get("/{report_card_id}", response_model=ReportCardResponse)
async def get_report_card(
    report_card_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await report_card_service.get_report_card(session, report_card_id)


@router.get("/exam/{exam_id}", response_model=list[ReportCardResponse])
async def get_exam_report_cards(
    exam_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_teacher(current_user)
    from app.repositories.report_card_repository import report_card_repository
    return await report_card_repository.get_by_exam(session, exam_id)
