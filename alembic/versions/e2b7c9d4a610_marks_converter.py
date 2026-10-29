"""Add board marks conversion rules and per-user history."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e2b7c9d4a610"
down_revision: Union[str, Sequence[str], None] = "4f84352b2529"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "marks_conversion_rules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("board_direction", sa.String(length=32), nullable=False),
        sa.Column("state", sa.String(length=80), nullable=False),
        sa.Column("class_grade", sa.String(length=32), nullable=False),
        sa.Column("subject", sa.String(length=120), nullable=True),
        sa.Column("exam_type", sa.String(length=80), nullable=False),
        sa.Column("academic_year", sa.String(length=20), nullable=False),
        sa.Column("source_max_marks", sa.Numeric(10, 2), nullable=False),
        sa.Column("target_max_marks", sa.Numeric(10, 2), nullable=False),
        sa.Column("method", sa.String(length=32), nullable=False),
        sa.Column("source_title", sa.String(length=255), nullable=True),
        sa.Column("reference_url", sa.String(length=2048), nullable=True),
        sa.Column("is_official", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("verified_by_id", sa.Uuid(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["verified_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_marks_rule_lookup",
        "marks_conversion_rules",
        ["board_direction", "state", "class_grade", "exam_type", "academic_year", "is_active"],
    )
    op.create_table(
        "marks_conversion_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("rule_id", sa.Uuid(), nullable=True),
        sa.Column("board_direction", sa.String(length=32), nullable=False),
        sa.Column("state", sa.String(length=80), nullable=False),
        sa.Column("class_grade", sa.String(length=32), nullable=False),
        sa.Column("subject", sa.String(length=120), nullable=True),
        sa.Column("exam_type", sa.String(length=80), nullable=False),
        sa.Column("academic_year", sa.String(length=20), nullable=False),
        sa.Column("marks_obtained", sa.Numeric(10, 2), nullable=False),
        sa.Column("source_max_marks", sa.Numeric(10, 2), nullable=False),
        sa.Column("target_marks", sa.Numeric(10, 2), nullable=False),
        sa.Column("target_max_marks", sa.Numeric(10, 2), nullable=False),
        sa.Column("percentage", sa.Numeric(7, 2), nullable=False),
        sa.Column("method", sa.String(length=64), nullable=False),
        sa.Column("is_official", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("formula", sa.String(length=255), nullable=False),
        sa.Column("source_title", sa.String(length=255), nullable=True),
        sa.Column("reference_url", sa.String(length=2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["rule_id"], ["marks_conversion_rules.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_marks_history_user_created", "marks_conversion_history", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_marks_history_user_created", table_name="marks_conversion_history")
    op.drop_table("marks_conversion_history")
    op.drop_index("ix_marks_rule_lookup", table_name="marks_conversion_rules")
    op.drop_table("marks_conversion_rules")
