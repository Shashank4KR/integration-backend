"""add entered_by to exam_results

Revision ID: c1e2d3f4a5b6
Revises: a9b8c7d6e5f4
Create Date: 2026-10-05 19:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c1e2d3f4a5b6'
down_revision: Union[str, None] = 'a9b8c7d6e5f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'exam_results',
        sa.Column('entered_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('exam_results', 'entered_by')
