"""Add updated_at column to marks_conversion_history table.

Revision ID: f3a1b2c4d5e6
Revises: e2b7c9d4a610
Create Date: 2026-11-07 12:08:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f3a1b2c4d5e6"
down_revision: Union[str, Sequence[str], None] = "e2b7c9d4a610"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "marks_conversion_history",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("marks_conversion_history", "updated_at")
