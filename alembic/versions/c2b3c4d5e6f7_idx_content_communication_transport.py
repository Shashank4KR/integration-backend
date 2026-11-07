"""Add foreign key indexes for content communication admissions and transport.

Revision ID: c2b3c4d5e6f7
Revises: c1a2b3c4d5e6
Create Date: 2026-11-07 14:40:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "c2b3c4d5e6f7"
down_revision: Union[str, Sequence[str], None] = "c1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('ix_lesson_plans_teacher_id', 'lesson_plans', ['teacher_id'], unique=False)
    op.create_index('ix_lesson_plans_class_id', 'lesson_plans', ['class_id'], unique=False)
    op.create_index('ix_lesson_plans_subject_id', 'lesson_plans', ['subject_id'], unique=False)
    op.create_index('ix_chapter_notes_teacher_id', 'chapter_notes', ['teacher_id'], unique=False)
    op.create_index('ix_chapter_notes_class_id', 'chapter_notes', ['class_id'], unique=False)
    op.create_index('ix_chapter_notes_subject_id', 'chapter_notes', ['subject_id'], unique=False)
    op.create_index('ix_content_resources_teacher_id', 'content_resources', ['teacher_id'], unique=False)
    op.create_index('ix_content_resources_class_id', 'content_resources', ['class_id'], unique=False)
    op.create_index('ix_content_resources_subject_id', 'content_resources', ['subject_id'], unique=False)
    op.create_index('ix_student_feedback_teacher_id', 'student_feedback', ['teacher_id'], unique=False)
    op.create_index('ix_student_feedback_student_id', 'student_feedback', ['student_id'], unique=False)
    op.create_index('ix_assignments_teacher_id', 'assignments', ['teacher_id'], unique=False)
    op.create_index('ix_assignments_class_id', 'assignments', ['class_id'], unique=False)
    op.create_index('ix_assignments_subject_id', 'assignments', ['subject_id'], unique=False)
    op.create_index('ix_assignment_submissions_assignment_id', 'assignment_submissions', ['assignment_id'], unique=False)
    op.create_index('ix_assignment_submissions_student_id', 'assignment_submissions', ['student_id'], unique=False)
    op.create_index('ix_announcements_created_by', 'announcements', ['created_by'], unique=False)
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'], unique=False)
    op.create_index('ix_messages_sender_id', 'messages', ['sender_id'], unique=False)
    op.create_index('ix_messages_receiver_id', 'messages', ['receiver_id'], unique=False)
    op.create_index('ix_events_created_by', 'events', ['created_by'], unique=False)
    op.create_index('ix_admission_applications_applied_class', 'admission_applications', ['applied_class'], unique=False)
    op.create_index('ix_admission_documents_application_id', 'admission_documents', ['application_id'], unique=False)
    op.create_index('ix_admission_documents_verified_by', 'admission_documents', ['verified_by'], unique=False)
    op.create_index('ix_leave_requests_user_id', 'leave_requests', ['user_id'], unique=False)
    op.create_index('ix_leave_requests_leave_type_id', 'leave_requests', ['leave_type_id'], unique=False)
    op.create_index('ix_leave_requests_approved_by', 'leave_requests', ['approved_by'], unique=False)
    op.create_index('ix_drivers_bus_id', 'drivers', ['bus_id'], unique=False)
    op.create_index('ix_route_stops_route_id', 'route_stops', ['route_id'], unique=False)
    op.create_index('ix_student_transport_student_id', 'student_transport', ['student_id'], unique=False)
    op.create_index('ix_student_transport_bus_id', 'student_transport', ['bus_id'], unique=False)
    op.create_index('ix_student_transport_route_id', 'student_transport', ['route_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_lesson_plans_teacher_id', table_name='lesson_plans')
    op.drop_index('ix_lesson_plans_class_id', table_name='lesson_plans')
    op.drop_index('ix_lesson_plans_subject_id', table_name='lesson_plans')
    op.drop_index('ix_chapter_notes_teacher_id', table_name='chapter_notes')
    op.drop_index('ix_chapter_notes_class_id', table_name='chapter_notes')
    op.drop_index('ix_chapter_notes_subject_id', table_name='chapter_notes')
    op.drop_index('ix_content_resources_teacher_id', table_name='content_resources')
    op.drop_index('ix_content_resources_class_id', table_name='content_resources')
    op.drop_index('ix_content_resources_subject_id', table_name='content_resources')
    op.drop_index('ix_student_feedback_teacher_id', table_name='student_feedback')
    op.drop_index('ix_student_feedback_student_id', table_name='student_feedback')
    op.drop_index('ix_assignments_teacher_id', table_name='assignments')
    op.drop_index('ix_assignments_class_id', table_name='assignments')
    op.drop_index('ix_assignments_subject_id', table_name='assignments')
    op.drop_index('ix_assignment_submissions_assignment_id', table_name='assignment_submissions')
    op.drop_index('ix_assignment_submissions_student_id', table_name='assignment_submissions')
    op.drop_index('ix_announcements_created_by', table_name='announcements')
    op.drop_index('ix_notifications_user_id', table_name='notifications')
    op.drop_index('ix_messages_sender_id', table_name='messages')
    op.drop_index('ix_messages_receiver_id', table_name='messages')
    op.drop_index('ix_events_created_by', table_name='events')
    op.drop_index('ix_admission_applications_applied_class', table_name='admission_applications')
    op.drop_index('ix_admission_documents_application_id', table_name='admission_documents')
    op.drop_index('ix_admission_documents_verified_by', table_name='admission_documents')
    op.drop_index('ix_leave_requests_user_id', table_name='leave_requests')
    op.drop_index('ix_leave_requests_leave_type_id', table_name='leave_requests')
    op.drop_index('ix_leave_requests_approved_by', table_name='leave_requests')
    op.drop_index('ix_drivers_bus_id', table_name='drivers')
    op.drop_index('ix_route_stops_route_id', table_name='route_stops')
    op.drop_index('ix_student_transport_student_id', table_name='student_transport')
    op.drop_index('ix_student_transport_bus_id', table_name='student_transport')
    op.drop_index('ix_student_transport_route_id', table_name='student_transport')
