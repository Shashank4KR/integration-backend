"""add maintenance_request_user_fk and check constraint

Revision ID: a9b8c7d6e5f4
Revises: e3f4a5b6c7d8
Create Date: 2026-10-03 18:58:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a9b8c7d6e5f4'
down_revision: Union[str, None] = 'e3f4a5b6c7d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Make requested_by nullable
    op.alter_column(
        'maintenance_requests',
        'requested_by',
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )

    # 2. Add requested_by_user_id with FK ondelete='SET NULL'
    op.add_column(
        'maintenance_requests',
        sa.Column('requested_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        'fk_maintenance_requests_requested_by_user_id',
        'maintenance_requests',
        'users',
        ['requested_by_user_id'],
        ['id'],
        ondelete='SET NULL',
    )

    # 3. Add CHECK constraint requiring at least one requester identifier
    op.create_check_constraint(
        'ck_maintenance_requests_requester_present',
        'maintenance_requests',
        'requested_by IS NOT NULL OR requested_by_user_id IS NOT NULL',
    )


def downgrade() -> None:
    # Note: Downgrade deletes maintenance requests that have no student ID associated,
    # rather than backfilling fake students, before restoring NOT NULL constraint on requested_by.
    op.drop_constraint('ck_maintenance_requests_requester_present', 'maintenance_requests', type_='check')
    op.drop_constraint('fk_maintenance_requests_requested_by_user_id', 'maintenance_requests', type_='foreignkey')
    op.drop_column('maintenance_requests', 'requested_by_user_id')

    op.execute("DELETE FROM maintenance_requests WHERE requested_by IS NULL")

    op.alter_column(
        'maintenance_requests',
        'requested_by',
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
