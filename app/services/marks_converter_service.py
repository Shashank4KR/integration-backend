from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marks_converter_model import MarksConversionHistory, MarksConversionRule
from app.models.user import User
from app.schemas.marks_converter_schema import BoardDirection, MarksConversionRequest

MARKS_QUANTUM = Decimal("0.01")
STATE_OPTIONS = [
    "Andhra Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat",
    "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
    "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
]
EXAM_TYPE_OPTIONS = ["Unit Test", "Periodic Test", "Half Yearly", "Pre Final", "Annual", "Board Examination", "Other"]


def calculate_marks(
    *,
    direction: BoardDirection,
    marks_obtained: Decimal,
    source_max_marks: Decimal,
    requested_target_max: Decimal,
    rule: MarksConversionRule | None = None,
) -> dict:
    """Calculate a proportional conversion and distinguish verified rules from estimates."""
    if source_max_marks <= 0 or requested_target_max <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Source and target maximum marks must be greater than zero")
    if marks_obtained < 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Marks obtained cannot be negative")
    if marks_obtained > source_max_marks:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Marks obtained cannot exceed the source maximum marks")

    is_official = bool(rule and rule.is_active and rule.is_official and rule.reference_url and rule.source_title)
    if is_official and source_max_marks != Decimal(rule.source_max_marks):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"The verified rule uses a source maximum of {rule.source_max_marks}; update the source maximum to match it.",
        )

    target_max = Decimal(rule.target_max_marks) if is_official else requested_target_max
    equivalent = (marks_obtained / source_max_marks * target_max).quantize(MARKS_QUANTUM, rounding=ROUND_HALF_UP)
    percentage = (marks_obtained / source_max_marks * Decimal("100")).quantize(MARKS_QUANTUM, rounding=ROUND_HALF_UP)
    formula = f"({marks_obtained} ÷ {source_max_marks}) × {target_max} = {equivalent}"
    method = "Verified board rule: proportional equivalence" if is_official else "Proportional mathematical estimate"
    return {
        "target_marks": equivalent,
        "target_max_marks": target_max,
        "percentage": percentage,
        "method": method,
        "formula": formula,
        "is_official": is_official,
        "status_note": (
            "Official equivalence based on the verified reference attached to this rule."
            if is_official
            else "Mathematical estimate only. No verified official equivalence rule is available for this selection."
        ),
        "source_title": rule.source_title if is_official else None,
        "reference_url": rule.reference_url if is_official else None,
        "rule_id": rule.id if is_official else None,
    }


async def find_applicable_rule(
    session: AsyncSession,
    payload: MarksConversionRequest,
) -> MarksConversionRule | None:
    """Choose an active, verified exact match, preferring subject-specific rules."""
    statement = select(MarksConversionRule).where(
        MarksConversionRule.board_direction == payload.board_direction.value,
        MarksConversionRule.state == payload.state.strip(),
        MarksConversionRule.class_grade == payload.class_grade.strip(),
        MarksConversionRule.exam_type == payload.exam_type.strip(),
        MarksConversionRule.academic_year == payload.academic_year.strip(),
        MarksConversionRule.is_active.is_(True),
        MarksConversionRule.is_official.is_(True),
    )
    subject = (payload.subject or "").strip()
    if subject:
        statement = statement.where(
            (MarksConversionRule.subject == subject) | (MarksConversionRule.subject.is_(None))
        )
    else:
        statement = statement.where(MarksConversionRule.subject.is_(None))
    statement = statement.order_by(MarksConversionRule.subject.is_not(None).desc(), MarksConversionRule.updated_at.desc())
    return (await session.execute(statement.limit(1))).scalar_one_or_none()


async def convert_and_store(
    session: AsyncSession,
    payload: MarksConversionRequest,
    user: User,
) -> dict:
    rule = await find_applicable_rule(session, payload)
    result = calculate_marks(
        direction=payload.board_direction,
        marks_obtained=payload.marks_obtained,
        source_max_marks=payload.source_max_marks,
        requested_target_max=payload.target_max_marks,
        rule=rule,
    )
    source_board, target_board = board_names(payload.board_direction, payload.state)
    history = MarksConversionHistory(
        user_id=user.id,
        rule_id=result["rule_id"],
        board_direction=payload.board_direction.value,
        state=payload.state.strip(),
        class_grade=payload.class_grade.strip(),
        subject=(payload.subject or "").strip() or None,
        exam_type=payload.exam_type.strip(),
        academic_year=payload.academic_year.strip(),
        marks_obtained=payload.marks_obtained,
        source_max_marks=payload.source_max_marks,
        target_marks=result["target_marks"],
        target_max_marks=result["target_max_marks"],
        percentage=result["percentage"],
        method=result["method"],
        is_official=result["is_official"],
        formula=result["formula"],
        source_title=result["source_title"],
        reference_url=result["reference_url"],
    )
    session.add(history)
    await session.commit()
    await session.refresh(history)
    return {
        "history_id": history.id,
        "board_direction": payload.board_direction,
        "source_board": source_board,
        "target_board": target_board,
        "state": history.state,
        "class_grade": history.class_grade,
        "subject": history.subject,
        "marks_obtained": history.marks_obtained,
        "source_max_marks": history.source_max_marks,
        "target_marks": history.target_marks,
        "target_max_marks": history.target_max_marks,
        "percentage": history.percentage,
        "method": result["method"],
        "formula": result["formula"],
        "is_official": history.is_official,
        "status_note": result["status_note"],
        "source_title": result["source_title"],
        "reference_url": result["reference_url"],
        "created_at": history.created_at or datetime.now(timezone.utc),
    }


def board_names(direction: BoardDirection, state: str) -> tuple[str, str]:
    state_board = f"{state.strip()} State Board"
    if direction == BoardDirection.CBSE_TO_STATE:
        return "CBSE", state_board
    return state_board, "CBSE"
