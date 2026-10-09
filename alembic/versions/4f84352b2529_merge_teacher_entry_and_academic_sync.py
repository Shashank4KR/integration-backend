"""merge teacher entry and academic sync

Revision ID: 4f84352b2529
Revises: c1e2d3f4a5b6, c2d4e6f8a103
Create Date: 2026-10-09 18:45:55.798053

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f84352b2529'
down_revision: Union[str, Sequence[str], None] = ('c1e2d3f4a5b6', 'c2d4e6f8a103')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
