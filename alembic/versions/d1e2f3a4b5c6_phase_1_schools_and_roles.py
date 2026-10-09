"""phase_1_schools_and_roles

Revision ID: d1e2f3a4b5c6
Revises: bc3edf744985
Create Date: 2026-10-01 21:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, Sequence[str], None] = 'bc3edf744985'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_SCHOOL_ID = '11111111-1111-1111-1111-111111111111'
SUPER_ADMIN_ROLE_ID = '00000000-0000-0000-0000-000000000008'

NULLABLE_TABLES = [
    "users",
    "login_history",
    "audit_logs",
    "notifications",
    "messages",
    "ai_chat_history",
    "system_settings",
]

SCHOOL_OWNED_TABLES = [
    "academic_calendar",
    "admins",
    "admission_applications",
    "admission_documents",
    "ai_analytics",
    "announcements",
    "assignment_submissions",
    "assignments",
    "attendance",
    "book_categories",
    "book_issues",
    "book_reservations",
    "books",
    "buses",
    "chapter_notes",
    "class_subjects",
    "classes",
    "content_resources",
    "departments",
    "drivers",
    "events",
    "exam_invigilators",
    "exam_results",
    "exam_subjects",
    "exam_timetables",
    "exams",
    "expense_categories",
    "expenses",
    "fee_installments",
    "fee_invoices",
    "fee_structures",
    "fine_payments",
    "hostel_allocations",
    "hostel_beds",
    "hostel_blocks",
    "hostel_complaints",
    "hostel_fee_invoices",
    "hostel_fee_structures",
    "hostel_leave_requests",
    "hostel_notices",
    "hostel_payments",
    "hostel_rooms",
    "hostel_settings",
    "hostel_visitors",
    "late_fee_rules",
    "leave_requests",
    "leave_types",
    "lesson_plans",
    "library_authors",
    "library_publishers",
    "library_settings",
    "maintenance_requests",
    "mess_attendance",
    "mess_collections",
    "mess_expenses",
    "mess_menu",
    "other_incomes",
    "parent_students",
    "parents",
    "payments",
    "refund_requests",
    "report_cards",
    "route_stops",
    "routes",
    "salaries",
    "scholarship_types",
    "student_categories",
    "student_fee_assignments",
    "student_feedback",
    "student_ledgers",
    "student_scholarships",
    "student_transport",
    "students",
    "subjects",
    "teacher_subjects",
    "teachers",
    "timetables",
    "work_orders",
]


def upgrade() -> None:
    # 1. Create schools table
    op.create_table(
        "schools",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("board", sa.String(length=100), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="ACTIVE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("code", name="uq_schools_code"),
    )

    # 2. Insert Default School
    op.execute(
        f"""
        INSERT INTO schools (id, name, code, board, address, logo_url, status)
        VALUES ('{DEFAULT_SCHOOL_ID}', 'Default School', 'DEFAULT', NULL, NULL, NULL, 'ACTIVE')
        ON CONFLICT (code) DO NOTHING;
        """
    )

    # 3. Create SUPER_ADMIN role (0008) in roles table
    op.execute(
        f"""
        INSERT INTO roles (id, role_name, description)
        VALUES ('{SUPER_ADMIN_ROLE_ID}', 'SUPER_ADMIN', 'Super Admin')
        ON CONFLICT (role_name) DO NOTHING;
        """
    )

    # 4. Add nullable school_id to the 7 nullable tables, backfill existing rows, add index & FK
    for table in NULLABLE_TABLES:
        op.add_column(table, sa.Column("school_id", sa.UUID(), nullable=True))
        op.execute(
            f"""
            UPDATE "{table}"
            SET school_id = '{DEFAULT_SCHOOL_ID}'
            WHERE school_id IS NULL;
            """
        )
        op.create_index(f"ix_{table}_school_id", table, ["school_id"])
        op.create_foreign_key(
            f"fk_{table}_school_id",
            table,
            "schools",
            ["school_id"],
            ["id"],
            ondelete="RESTRICT",
        )

    # 5. Add NOT NULL school_id with server_default to the 78 school-owned tables, index & FK
    for table in SCHOOL_OWNED_TABLES:
        op.add_column(
            table,
            sa.Column(
                "school_id",
                sa.UUID(),
                server_default=sa.text(f"'{DEFAULT_SCHOOL_ID}'"),
                nullable=False,
            ),
        )
        op.create_index(f"ix_{table}_school_id", table, ["school_id"])
        op.create_foreign_key(
            f"fk_{table}_school_id",
            table,
            "schools",
            ["school_id"],
            ["id"],
            ondelete="RESTRICT",
        )


def downgrade() -> None:
    # 1. Drop foreign keys, indexes, and school_id columns on school-owned tables
    for table in SCHOOL_OWNED_TABLES:
        op.drop_constraint(f"fk_{table}_school_id", table, type_="foreignkey")
        op.drop_index(f"ix_{table}_school_id", table_name=table)
        op.drop_column(table, "school_id")

    # 2. Drop foreign keys, indexes, and school_id columns on nullable tables
    for table in NULLABLE_TABLES:
        op.drop_constraint(f"fk_{table}_school_id", table, type_="foreignkey")
        op.drop_index(f"ix_{table}_school_id", table_name=table)
        op.drop_column(table, "school_id")

    # 3. Remove SUPER_ADMIN role
    op.execute(
        f"""
        DELETE FROM roles
        WHERE role_name = 'SUPER_ADMIN' OR id = '{SUPER_ADMIN_ROLE_ID}';
        """
    )

    # 4. Drop schools table
    op.drop_table("schools")
