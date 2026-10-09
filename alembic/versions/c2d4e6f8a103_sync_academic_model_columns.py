"""sync academic model columns with existing database

Revision ID: c2d4e6f8a103
Revises: f9a8b7c6d5e4
Create Date: 2026-10-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c2d4e6f8a103"
down_revision: Union[str, Sequence[str], None] = "f9a8b7c6d5e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "classes",
        sa.Column("room_number", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "classes",
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=True,
            server_default="ACTIVE",
        ),
    )
    op.add_column(
        "subjects",
        sa.Column("department_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_subjects_department_id_departments",
        "subjects",
        "departments",
        ["department_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_subjects_department_id_departments",
        "subjects",
        type_="foreignkey",
    )
    op.drop_column("subjects", "department_id")
    op.drop_column("classes", "status")
    op.drop_column("classes", "room_number")
