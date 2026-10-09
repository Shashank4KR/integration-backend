"""security_and_audit_timestamps

Revision ID: bc3edf744985
Revises: 63ff3db91215
Create Date: 2026-09-20 11:33:01.108005

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bc3edf744985'
down_revision: Union[str, Sequence[str], None] = '63ff3db91215'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. User security controls
    op.add_column("users", sa.Column("must_change_password", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.add_column("users", sa.Column("failed_login_attempts", sa.Integer(), server_default=sa.text("0"), nullable=False))
    op.add_column("users", sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))

    # 2. Add created_at and updated_at to models missing both
    tables_both = [
        "admins",
        "students",
        "teachers",
        "parents",
        "departments",
        "parent_students",
        "role_permissions",
    ]
    for table in tables_both:
        op.add_column(table, sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
        op.add_column(table, sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))

    # 3. Add updated_at to models that already have created_at
    tables_updated_only = [
        "class_subjects",
        "exam_subjects",
        "exam_invigilators",
        "exam_timetables",
        "student_ledgers",
        "teacher_subjects",
    ]
    for table in tables_updated_only:
        op.add_column(table, sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))


def downgrade() -> None:
    tables_updated_only = [
        "class_subjects",
        "exam_subjects",
        "exam_invigilators",
        "exam_timetables",
        "student_ledgers",
        "teacher_subjects",
    ]
    for table in tables_updated_only:
        op.drop_column(table, "updated_at")

    tables_both = [
        "admins",
        "students",
        "teachers",
        "parents",
        "departments",
        "parent_students",
        "role_permissions",
    ]
    for table in tables_both:
        op.drop_column(table, "updated_at")
        op.drop_column(table, "created_at")

    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_attempts")
    op.drop_column("users", "must_change_password")
