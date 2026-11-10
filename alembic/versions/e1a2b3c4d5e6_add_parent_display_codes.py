"""add stable human-readable parent codes"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "d5e6f7a8b9c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SEQUENCE parent_code_seq START WITH 1")
    op.add_column(
        "parents", sa.Column("parent_code", sa.String(length=16), nullable=True)
    )
    op.execute(
        "UPDATE parents SET parent_code = 'P-' || "
        "lpad(nextval('parent_code_seq')::text, 3, '0')"
    )
    op.alter_column("parents", "parent_code", nullable=False)
    op.create_unique_constraint("uq_parents_parent_code", "parents", ["parent_code"])


def downgrade() -> None:
    op.drop_constraint("uq_parents_parent_code", "parents", type_="unique")
    op.drop_column("parents", "parent_code")
    op.execute("DROP SEQUENCE parent_code_seq")
