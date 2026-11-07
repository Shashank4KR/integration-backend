"""Add foreign key indexes for finance fees salaries and library.

Revision ID: c3c4d5e6f7a8
Revises: c2b3c4d5e6f7
Create Date: 2026-11-07 14:40:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "c3c4d5e6f7a8"
down_revision: Union[str, Sequence[str], None] = "c2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('ix_fee_structures_class_id', 'fee_structures', ['class_id'], unique=False)
    op.create_index('ix_fee_structures_student_category_id', 'fee_structures', ['student_category_id'], unique=False)
    op.create_index('ix_fee_installments_fee_structure_id', 'fee_installments', ['fee_structure_id'], unique=False)
    op.create_index('ix_fee_invoices_student_id', 'fee_invoices', ['student_id'], unique=False)
    op.create_index('ix_fee_invoices_fee_type_id', 'fee_invoices', ['fee_type_id'], unique=False)
    op.create_index('ix_fee_invoices_assignment_id', 'fee_invoices', ['assignment_id'], unique=False)
    op.create_index('ix_student_fee_assignments_student_id', 'student_fee_assignments', ['student_id'], unique=False)
    op.create_index('ix_student_fee_assignments_fee_structure_id', 'student_fee_assignments', ['fee_structure_id'], unique=False)
    op.create_index('ix_student_fee_assignments_student_category_id', 'student_fee_assignments', ['student_category_id'], unique=False)
    op.create_index('ix_student_ledgers_student_id', 'student_ledgers', ['student_id'], unique=False)
    op.create_index('ix_student_scholarships_student_id', 'student_scholarships', ['student_id'], unique=False)
    op.create_index('ix_student_scholarships_scholarship_type_id', 'student_scholarships', ['scholarship_type_id'], unique=False)
    op.create_index('ix_student_scholarships_approved_by', 'student_scholarships', ['approved_by'], unique=False)
    op.create_index('ix_late_fee_rules_fee_structure_id', 'late_fee_rules', ['fee_structure_id'], unique=False)
    op.create_index('ix_payments_invoice_id', 'payments', ['invoice_id'], unique=False)
    op.create_index('ix_payments_processed_by', 'payments', ['processed_by'], unique=False)
    op.create_index('ix_refund_requests_student_id', 'refund_requests', ['student_id'], unique=False)
    op.create_index('ix_refund_requests_payment_id', 'refund_requests', ['payment_id'], unique=False)
    op.create_index('ix_refund_requests_invoice_id', 'refund_requests', ['invoice_id'], unique=False)
    op.create_index('ix_refund_requests_approved_by', 'refund_requests', ['approved_by'], unique=False)
    op.create_index('ix_refund_requests_created_by', 'refund_requests', ['created_by'], unique=False)
    op.create_index('ix_expenses_expense_category_id', 'expenses', ['expense_category_id'], unique=False)
    op.create_index('ix_expenses_approved_by', 'expenses', ['approved_by'], unique=False)
    op.create_index('ix_expenses_created_by', 'expenses', ['created_by'], unique=False)
    op.create_index('ix_salaries_approved_by', 'salaries', ['approved_by'], unique=False)
    op.create_index('ix_salaries_created_by', 'salaries', ['created_by'], unique=False)
    op.create_index('ix_other_incomes_created_by', 'other_incomes', ['created_by'], unique=False)
    op.create_index('ix_books_author_id', 'books', ['author_id'], unique=False)
    op.create_index('ix_books_publisher_id', 'books', ['publisher_id'], unique=False)
    op.create_index('ix_books_category_id', 'books', ['category_id'], unique=False)
    op.create_index('ix_book_issues_book_id', 'book_issues', ['book_id'], unique=False)
    op.create_index('ix_book_issues_student_id', 'book_issues', ['student_id'], unique=False)
    op.create_index('ix_book_reservations_book_id', 'book_reservations', ['book_id'], unique=False)
    op.create_index('ix_book_reservations_student_id', 'book_reservations', ['student_id'], unique=False)
    op.create_index('ix_fine_payments_issue_id', 'fine_payments', ['issue_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_fee_structures_class_id', table_name='fee_structures')
    op.drop_index('ix_fee_structures_student_category_id', table_name='fee_structures')
    op.drop_index('ix_fee_installments_fee_structure_id', table_name='fee_installments')
    op.drop_index('ix_fee_invoices_student_id', table_name='fee_invoices')
    op.drop_index('ix_fee_invoices_fee_type_id', table_name='fee_invoices')
    op.drop_index('ix_fee_invoices_assignment_id', table_name='fee_invoices')
    op.drop_index('ix_student_fee_assignments_student_id', table_name='student_fee_assignments')
    op.drop_index('ix_student_fee_assignments_fee_structure_id', table_name='student_fee_assignments')
    op.drop_index('ix_student_fee_assignments_student_category_id', table_name='student_fee_assignments')
    op.drop_index('ix_student_ledgers_student_id', table_name='student_ledgers')
    op.drop_index('ix_student_scholarships_student_id', table_name='student_scholarships')
    op.drop_index('ix_student_scholarships_scholarship_type_id', table_name='student_scholarships')
    op.drop_index('ix_student_scholarships_approved_by', table_name='student_scholarships')
    op.drop_index('ix_late_fee_rules_fee_structure_id', table_name='late_fee_rules')
    op.drop_index('ix_payments_invoice_id', table_name='payments')
    op.drop_index('ix_payments_processed_by', table_name='payments')
    op.drop_index('ix_refund_requests_student_id', table_name='refund_requests')
    op.drop_index('ix_refund_requests_payment_id', table_name='refund_requests')
    op.drop_index('ix_refund_requests_invoice_id', table_name='refund_requests')
    op.drop_index('ix_refund_requests_approved_by', table_name='refund_requests')
    op.drop_index('ix_refund_requests_created_by', table_name='refund_requests')
    op.drop_index('ix_expenses_expense_category_id', table_name='expenses')
    op.drop_index('ix_expenses_approved_by', table_name='expenses')
    op.drop_index('ix_expenses_created_by', table_name='expenses')
    op.drop_index('ix_salaries_approved_by', table_name='salaries')
    op.drop_index('ix_salaries_created_by', table_name='salaries')
    op.drop_index('ix_other_incomes_created_by', table_name='other_incomes')
    op.drop_index('ix_books_author_id', table_name='books')
    op.drop_index('ix_books_publisher_id', table_name='books')
    op.drop_index('ix_books_category_id', table_name='books')
    op.drop_index('ix_book_issues_book_id', table_name='book_issues')
    op.drop_index('ix_book_issues_student_id', table_name='book_issues')
    op.drop_index('ix_book_reservations_book_id', table_name='book_reservations')
    op.drop_index('ix_book_reservations_student_id', table_name='book_reservations')
    op.drop_index('ix_fine_payments_issue_id', table_name='fine_payments')
