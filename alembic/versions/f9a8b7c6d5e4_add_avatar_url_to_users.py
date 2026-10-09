"""add_avatar_url_to_users

Revision ID: f9a8b7c6d5e4
Revises: a9b8c7d6e5f4
Create Date: 2026-10-04 15:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
# pyrefly: ignore [missing-import]
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f9a8b7c6d5e4'
down_revision: Union[str, Sequence[str], None] = 'a9b8c7d6e5f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('avatar_url', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'avatar_url')
