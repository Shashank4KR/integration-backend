from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.models.marks_converter_model import MarksConversionHistory, MarksConversionRule
from app.models.subject_model import Subject
from app.models.user import User
from app.schemas.marks_converter_schema import (
    MarksConversionRequest,
    MarksConversionResult,
    MarksConversionRuleCreate,
    MarksConversionRuleResponse,
    MarksConversionRuleUpdate,
)
from app.services.marks_converter_service import (
    EXAM_TYPE_OPTIONS,
    STATE_OPTIONS,
    convert_and_store,
)

router = APIRouter()


def _ensure_admin(user: User) -> None:
    role_name = (user.role.role_name if user.role else "").upper()
    if role_name not in {"ADMIN", "SUPER_ADMIN", "SUPERADMIN"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administrators can manage conversion rules")


async def _ensure_no_duplicate_active_rule(session: AsyncSession, values: dict, exclude_id: UUID | None = None) -> None:
    if not values.get("is_active", True):
        return
    filters = [
        MarksConversionRule.is_active.is_(True),
        MarksConversionRule.board_direction == values["board_direction"],
        MarksConversionRule.state == values["state"],
        MarksConversionRule.class_grade == values["class_grade"],
        MarksConversionRule.subject == values["subject"] if values["subject"] is not None else MarksConversionRule.subject.is_(None),
        MarksConversionRule.exam_type == values["exam_type"],
        MarksConversionRule.academic_year == values["academic_year"],
    ]
    statement = select(MarksConversionRule.id).where(*filters)
    if exclude_id is not None:
        statement = statement.where(MarksConversionRule.id != exclude_id)
    if (await session.execute(statement.limit(1))).scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An active rule already exists for this board, state, class, subject, exam type, and academic year")


@router.get("/options")
async def get_options(
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    has_verified_rules = (
        await session.execute(
            select(MarksConversionRule.id)
            .where(MarksConversionRule.is_active.is_(True), MarksConversionRule.is_official.is_(True))
            .limit(1)
        )
    ).scalar_one_or_none() is not None
    subjects = (
        await session.execute(
            select(Subject.subject_name)
            .where(Subject.status == "ACTIVE")
            .distinct()
            .order_by(Subject.subject_name)
        )
    ).scalars().all()
    return {
        "states": STATE_OPTIONS,
        "classes": [f"Class {grade}" for grade in range(1, 13)],
        "exam_types": EXAM_TYPE_OPTIONS,
        "subjects": subjects,
        "methods": [{"id": "PROPORTIONAL", "label": "Proportional scaling"}],
        "official_rules_available": has_verified_rules,
    }


@router.post("/convert", response_model=MarksConversionResult)
async def convert_marks(
    payload: MarksConversionRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await convert_and_store(session, payload, current_user)


@router.get("/history")
async def get_history(
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    result = await session.execute(
        select(MarksConversionHistory)
        .where(MarksConversionHistory.user_id == current_user.id)
        .order_by(MarksConversionHistory.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return [
        {
            "id": row.id,
            "board_direction": row.board_direction,
            "state": row.state,
            "class_grade": row.class_grade,
            "subject": row.subject,
            "marks_obtained": row.marks_obtained,
            "source_max_marks": row.source_max_marks,
            "target_marks": row.target_marks,
            "target_max_marks": row.target_max_marks,
            "percentage": row.percentage,
            "method": row.method,
            "is_official": row.is_official,
            "formula": row.formula,
            "source_title": row.source_title,
            "reference_url": row.reference_url,
            "created_at": row.created_at,
        }
        for row in result.scalars().all()
    ]


@router.get("/rules", response_model=list[MarksConversionRuleResponse])
async def list_rules(
    include_inactive: bool = False,
    limit: int = Query(default=100, ge=1, le=250),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if include_inactive:
        _ensure_admin(current_user)
    statement = select(MarksConversionRule)
    if not include_inactive:
        statement = statement.where(MarksConversionRule.is_active.is_(True), MarksConversionRule.is_official.is_(True))
    statement = statement.order_by(MarksConversionRule.state, MarksConversionRule.class_grade, MarksConversionRule.subject).offset(offset).limit(limit)
    return (await session.execute(statement)).scalars().all()


@router.post("/rules", response_model=MarksConversionRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    payload: MarksConversionRuleCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    data = payload.model_dump()
    if data["reference_url"] is not None:
        data["reference_url"] = str(data["reference_url"])
    if data["is_official"]:
        data["verified_by_id"] = current_user.id
        data["verified_at"] = datetime.now(timezone.utc)
    data["created_by_id"] = current_user.id
    data["state"] = data["state"].strip()
    data["class_grade"] = data["class_grade"].strip()
    data["exam_type"] = data["exam_type"].strip()
    data["academic_year"] = data["academic_year"].strip()
    data["subject"] = (data["subject"] or "").strip() or None
    await _ensure_no_duplicate_active_rule(session, data)
    rule = MarksConversionRule(**data)
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return rule


@router.put("/rules/{rule_id}", response_model=MarksConversionRuleResponse)
async def update_rule(
    rule_id: UUID,
    payload: MarksConversionRuleUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    rule = await session.get(MarksConversionRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversion rule not found")
    changes = payload.model_dump(exclude_unset=True)
    next_is_official = changes.get("is_official", rule.is_official)
    next_title = changes.get("source_title", rule.source_title)
    next_url = changes.get("reference_url", rule.reference_url)
    if next_is_official and (not next_title or not next_url):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Official rules require a document title and reference URL")
    if "reference_url" in changes and changes["reference_url"] is not None:
        changes["reference_url"] = str(changes["reference_url"])
    if "is_official" in changes:
        changes["verified_by_id"] = current_user.id if next_is_official else None
        changes["verified_at"] = datetime.now(timezone.utc) if next_is_official else None
    elif next_is_official and any(
        key in changes
        for key in (
            "board_direction",
            "state",
            "class_grade",
            "subject",
            "exam_type",
            "academic_year",
            "source_max_marks",
            "target_max_marks",
            "method",
            "source_title",
            "reference_url",
        )
    ):
        changes["verified_by_id"] = current_user.id
        changes["verified_at"] = datetime.now(timezone.utc)
    for key in ("state", "class_grade", "exam_type", "academic_year"):
        if key in changes and changes[key] is not None:
            changes[key] = changes[key].strip()
    if "subject" in changes:
        changes["subject"] = (changes["subject"] or "").strip() or None
    for key, value in changes.items():
        setattr(rule, key, value)
    await _ensure_no_duplicate_active_rule(
        session,
        {
            "is_active": rule.is_active,
            "board_direction": rule.board_direction,
            "state": rule.state,
            "class_grade": rule.class_grade,
            "subject": rule.subject,
            "exam_type": rule.exam_type,
            "academic_year": rule.academic_year,
        },
        exclude_id=rule.id,
    )
    await session.commit()
    await session.refresh(rule)
    return rule
