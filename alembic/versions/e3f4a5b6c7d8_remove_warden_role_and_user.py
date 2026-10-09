"""remove_warden_role_and_user

Revision ID: e3f4a5b6c7d8
Revises: d1e2f3a4b5c6
Create Date: 2026-10-03 18:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3f4a5b6c7d8'
down_revision: Union[str, Sequence[str], None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

WARDEN_USER_ID = '00000000-0000-0000-0000-000000000077'
WARDEN_ROLE_ID = '00000000-0000-0000-0000-000000000007'


def upgrade() -> None:
    # 1. Reassign work_orders.assigned_to away from warden user to school ADMIN user
    op.execute(f"""
        UPDATE work_orders
        SET assigned_to = (
            SELECT u.id
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE r.role_name = 'ADMIN'
            ORDER BY u.created_at ASC
            LIMIT 1
        )
        WHERE assigned_to = '{WARDEN_USER_ID}';
    """)

    # 2. Clear hostel_blocks.warden_id
    op.execute(f"""
        UPDATE hostel_blocks
        SET warden_id = NULL
        WHERE warden_id = '{WARDEN_USER_ID}';
    """)

    # 3. Clean up audit logs, login history, notifications, messages for warden user to avoid FK violations
    op.execute(f"""
        DELETE FROM login_history WHERE user_id = '{WARDEN_USER_ID}';
    """)
    op.execute(f"""
        DELETE FROM audit_logs WHERE user_id = '{WARDEN_USER_ID}';
    """)
    op.execute(f"""
        DELETE FROM messages WHERE sender_id = '{WARDEN_USER_ID}' OR receiver_id = '{WARDEN_USER_ID}';
    """)
    op.execute(f"""
        DELETE FROM notifications WHERE user_id = '{WARDEN_USER_ID}';
    """)

    # 4. Delete warden user
    op.execute(f"""
        DELETE FROM users WHERE id = '{WARDEN_USER_ID}' OR username = 'warden';
    """)

    # 5. Delete role_permissions for WARDEN role (if any exist)
    op.execute(f"""
        DELETE FROM role_permissions WHERE role_id = '{WARDEN_ROLE_ID}';
    """)

    # 6. Delete WARDEN role
    op.execute(f"""
        DELETE FROM roles WHERE id = '{WARDEN_ROLE_ID}' OR role_name = 'WARDEN';
    """)


def downgrade() -> None:
    op.execute(f"""
        DO $$
        BEGIN
            INSERT INTO roles (id, role_name, description, created_at, updated_at)
            VALUES (
                '{WARDEN_ROLE_ID}',
                'WARDEN',
                'Hostel and mess warden',
                NOW(),
                NOW()
            )
            ON CONFLICT (id) DO NOTHING;

            INSERT INTO users (id, username, email, password_hash, role_id, status, created_at, updated_at, school_id)
            SELECT
                '{WARDEN_USER_ID}',
                'warden',
                'warden@example.com',
                '$2b$12$e80MvYJ.Pj1n42yBqPphv.E0Q0vH10hB562H9z1h5b2Ew4F6XgC1m',
                '{WARDEN_ROLE_ID}',
                TRUE,
                NOW(),
                NOW(),
                (SELECT id FROM schools LIMIT 1)
            WHERE NOT EXISTS (SELECT 1 FROM users WHERE id = '{WARDEN_USER_ID}');
        END $$;
    """)
