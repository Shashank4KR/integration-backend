from decimal import Decimal
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from fastapi import HTTPException

from app.schemas.marks_converter_schema import BoardDirection, MarksConversionRequest
from app.services.marks_converter_service import calculate_marks


def test_cbse_to_state_board_uses_proportional_estimate_when_rule_missing():
    result = calculate_marks(
        direction=BoardDirection.CBSE_TO_STATE,
        marks_obtained=Decimal("80"),
        source_max_marks=Decimal("100"),
        requested_target_max=Decimal("80"),
    )

    assert result["target_marks"] == Decimal("64.00")
    assert result["target_max_marks"] == Decimal("80")
    assert result["percentage"] == Decimal("80.00")
    assert result["is_official"] is False
    assert "estimate" in result["status_note"].lower()


def test_state_board_to_cbse_uses_selected_verified_board_rule():
    rule = SimpleNamespace(
        is_active=True,
        is_official=True,
        source_max_marks=Decimal("80"),
        target_max_marks=Decimal("100"),
        source_title="State board assessment circular",
        reference_url="https://board.example/rules",
        id="rule-id",
    )

    result = calculate_marks(
        direction=BoardDirection.STATE_TO_CBSE,
        marks_obtained=Decimal("64"),
        source_max_marks=Decimal("80"),
        requested_target_max=Decimal("90"),
        rule=rule,
    )

    assert result["target_marks"] == Decimal("80.00")
    assert result["target_max_marks"] == Decimal("100")
    assert result["is_official"] is True
    assert result["reference_url"] == "https://board.example/rules"


@pytest.mark.parametrize(
    ("marks", "source_max", "target_max", "message"),
    [
        (Decimal("-0.01"), Decimal("100"), Decimal("100"), "cannot be negative"),
        (Decimal("101"), Decimal("100"), Decimal("100"), "cannot exceed"),
        (Decimal("10"), Decimal("0"), Decimal("100"), "greater than zero"),
        (Decimal("10"), Decimal("100"), Decimal("0"), "greater than zero"),
    ],
)
def test_invalid_values_are_rejected(marks, source_max, target_max, message):
    with pytest.raises(HTTPException, match=message):
        calculate_marks(
            direction=BoardDirection.CBSE_TO_STATE,
            marks_obtained=marks,
            source_max_marks=source_max,
            requested_target_max=target_max,
        )


def test_decimal_marks_round_half_up_to_two_decimal_places():
    result = calculate_marks(
        direction=BoardDirection.CBSE_TO_STATE,
        marks_obtained=Decimal("1.00"),
        source_max_marks=Decimal("2.00"),
        requested_target_max=Decimal("2.01"),
    )

    assert result["target_marks"] == Decimal("1.01")


def test_conversion_request_rejects_marks_above_maximum():
    with pytest.raises(ValidationError, match="cannot exceed"):
        MarksConversionRequest(
            board_direction=BoardDirection.CBSE_TO_STATE,
            state="Karnataka",
            class_grade="Class 10",
            exam_type="Annual",
            academic_year="2026-2027",
            marks_obtained=101,
            source_max_marks=100,
            target_max_marks=100,
        )


def test_verified_rule_with_wrong_source_maximum_is_not_silently_applied():
    rule = SimpleNamespace(
        is_active=True,
        is_official=True,
        source_max_marks=Decimal("80"),
        target_max_marks=Decimal("100"),
        source_title="Verified circular",
        reference_url="https://board.example/rules",
        id="rule-id",
    )

    with pytest.raises(HTTPException, match="source maximum of 80"):
        calculate_marks(
            direction=BoardDirection.STATE_TO_CBSE,
            marks_obtained=Decimal("60"),
            source_max_marks=Decimal("100"),
            requested_target_max=Decimal("100"),
            rule=rule,
        )
