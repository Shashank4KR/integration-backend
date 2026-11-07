"""Add foreign key indexes for hostel and maintenance operations.

Revision ID: c4d5e6f7a8b9
Revises: c3c4d5e6f7a8
Create Date: 2026-11-07 14:40:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, Sequence[str], None] = "c3c4d5e6f7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('ix_hostel_blocks_warden_id', 'hostel_blocks', ['warden_id'], unique=False)
    op.create_index('ix_hostel_rooms_block_id', 'hostel_rooms', ['block_id'], unique=False)
    op.create_index('ix_hostel_beds_room_id', 'hostel_beds', ['room_id'], unique=False)
    op.create_index('ix_hostel_fee_invoices_student_id', 'hostel_fee_invoices', ['student_id'], unique=False)
    op.create_index('ix_hostel_fee_invoices_hostel_fee_id', 'hostel_fee_invoices', ['hostel_fee_id'], unique=False)
    op.create_index('ix_hostel_payments_invoice_id', 'hostel_payments', ['invoice_id'], unique=False)
    op.create_index('ix_hostel_complaints_student_id', 'hostel_complaints', ['student_id'], unique=False)
    op.create_index('ix_hostel_complaints_assigned_to', 'hostel_complaints', ['assigned_to'], unique=False)
    op.create_index('ix_hostel_complaints_resolved_by', 'hostel_complaints', ['resolved_by'], unique=False)
    op.create_index('ix_hostel_leave_requests_student_id', 'hostel_leave_requests', ['student_id'], unique=False)
    op.create_index('ix_hostel_leave_requests_allocation_id', 'hostel_leave_requests', ['allocation_id'], unique=False)
    op.create_index('ix_hostel_leave_requests_approved_by', 'hostel_leave_requests', ['approved_by'], unique=False)
    op.create_index('ix_hostel_notices_published_by', 'hostel_notices', ['published_by'], unique=False)
    op.create_index('ix_hostel_visitors_student_id', 'hostel_visitors', ['student_id'], unique=False)
    op.create_index('ix_hostel_visitors_approved_by', 'hostel_visitors', ['approved_by'], unique=False)
    op.create_index('ix_mess_attendance_student_id', 'mess_attendance', ['student_id'], unique=False)
    op.create_index('ix_mess_collections_student_id', 'mess_collections', ['student_id'], unique=False)
    op.create_index('ix_mess_collections_received_by', 'mess_collections', ['received_by'], unique=False)
    op.create_index('ix_mess_menu_created_by', 'mess_menu', ['created_by'], unique=False)
    op.create_index('ix_maintenance_requests_requested_by', 'maintenance_requests', ['requested_by'], unique=False)
    op.create_index('ix_maintenance_requests_requested_by_user_id', 'maintenance_requests', ['requested_by_user_id'], unique=False)
    op.create_index('ix_maintenance_requests_room_id', 'maintenance_requests', ['room_id'], unique=False)
    op.create_index('ix_work_orders_request_id', 'work_orders', ['request_id'], unique=False)
    op.create_index('ix_work_orders_assigned_to', 'work_orders', ['assigned_to'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_hostel_blocks_warden_id', table_name='hostel_blocks')
    op.drop_index('ix_hostel_rooms_block_id', table_name='hostel_rooms')
    op.drop_index('ix_hostel_beds_room_id', table_name='hostel_beds')
    op.drop_index('ix_hostel_fee_invoices_student_id', table_name='hostel_fee_invoices')
    op.drop_index('ix_hostel_fee_invoices_hostel_fee_id', table_name='hostel_fee_invoices')
    op.drop_index('ix_hostel_payments_invoice_id', table_name='hostel_payments')
    op.drop_index('ix_hostel_complaints_student_id', table_name='hostel_complaints')
    op.drop_index('ix_hostel_complaints_assigned_to', table_name='hostel_complaints')
    op.drop_index('ix_hostel_complaints_resolved_by', table_name='hostel_complaints')
    op.drop_index('ix_hostel_leave_requests_student_id', table_name='hostel_leave_requests')
    op.drop_index('ix_hostel_leave_requests_allocation_id', table_name='hostel_leave_requests')
    op.drop_index('ix_hostel_leave_requests_approved_by', table_name='hostel_leave_requests')
    op.drop_index('ix_hostel_notices_published_by', table_name='hostel_notices')
    op.drop_index('ix_hostel_visitors_student_id', table_name='hostel_visitors')
    op.drop_index('ix_hostel_visitors_approved_by', table_name='hostel_visitors')
    op.drop_index('ix_mess_attendance_student_id', table_name='mess_attendance')
    op.drop_index('ix_mess_collections_student_id', table_name='mess_collections')
    op.drop_index('ix_mess_collections_received_by', table_name='mess_collections')
    op.drop_index('ix_mess_menu_created_by', table_name='mess_menu')
    op.drop_index('ix_maintenance_requests_requested_by', table_name='maintenance_requests')
    op.drop_index('ix_maintenance_requests_requested_by_user_id', table_name='maintenance_requests')
    op.drop_index('ix_maintenance_requests_room_id', table_name='maintenance_requests')
    op.drop_index('ix_work_orders_request_id', table_name='work_orders')
    op.drop_index('ix_work_orders_assigned_to', table_name='work_orders')
