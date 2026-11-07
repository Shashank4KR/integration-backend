"""Add foreign key indexes for core users and academics.

Revision ID: c1a2b3c4d5e6
Revises: b3c4d5e6f7a8
Create Date: 2026-11-07 14:40:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "c1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "b3c4d5e6f7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('ix_users_role_id', 'users', ['role_id'], unique=False)
    op.create_index('ix_admins_user_id', 'admins', ['user_id'], unique=False)
    op.create_index('ix_teachers_user_id', 'teachers', ['user_id'], unique=False)
    op.create_index('ix_teachers_department_id', 'teachers', ['department_id'], unique=False)
    op.create_index('ix_parents_user_id', 'parents', ['user_id'], unique=False)
    op.create_index('ix_students_user_id', 'students', ['user_id'], unique=False)
    op.create_index('ix_students_class_id', 'students', ['class_id'], unique=False)
    op.create_index('ix_parent_students_parent_id', 'parent_students', ['parent_id'], unique=False)
    op.create_index('ix_parent_students_student_id', 'parent_students', ['student_id'], unique=False)
    op.create_index('ix_classes_class_teacher_id', 'classes', ['class_teacher_id'], unique=False)
    op.create_index('ix_subjects_department_id', 'subjects', ['department_id'], unique=False)
    op.create_index('ix_class_subjects_class_id', 'class_subjects', ['class_id'], unique=False)
    op.create_index('ix_class_subjects_subject_id', 'class_subjects', ['subject_id'], unique=False)
    op.create_index('ix_teacher_subjects_teacher_id', 'teacher_subjects', ['teacher_id'], unique=False)
    op.create_index('ix_teacher_subjects_subject_id', 'teacher_subjects', ['subject_id'], unique=False)
    op.create_index('ix_teacher_subjects_class_id', 'teacher_subjects', ['class_id'], unique=False)
    op.create_index('ix_timetables_class_id', 'timetables', ['class_id'], unique=False)
    op.create_index('ix_timetables_subject_id', 'timetables', ['subject_id'], unique=False)
    op.create_index('ix_timetables_teacher_id', 'timetables', ['teacher_id'], unique=False)
    op.create_index('ix_attendance_student_id', 'attendance', ['student_id'], unique=False)
    op.create_index('ix_attendance_class_id', 'attendance', ['class_id'], unique=False)
    op.create_index('ix_attendance_subject_id', 'attendance', ['subject_id'], unique=False)
    op.create_index('ix_attendance_teacher_id', 'attendance', ['teacher_id'], unique=False)
    op.create_index('ix_attendance_marked_by', 'attendance', ['marked_by'], unique=False)
    op.create_index('ix_exams_class_id', 'exams', ['class_id'], unique=False)
    op.create_index('ix_exam_invigilators_exam_id', 'exam_invigilators', ['exam_id'], unique=False)
    op.create_index('ix_exam_invigilators_teacher_id', 'exam_invigilators', ['teacher_id'], unique=False)
    op.create_index('ix_exam_results_exam_id', 'exam_results', ['exam_id'], unique=False)
    op.create_index('ix_exam_results_student_id', 'exam_results', ['student_id'], unique=False)
    op.create_index('ix_exam_results_subject_id', 'exam_results', ['subject_id'], unique=False)
    op.create_index('ix_exam_results_entered_by', 'exam_results', ['entered_by'], unique=False)
    op.create_index('ix_exam_subjects_exam_id', 'exam_subjects', ['exam_id'], unique=False)
    op.create_index('ix_exam_subjects_subject_id', 'exam_subjects', ['subject_id'], unique=False)
    op.create_index('ix_exam_timetables_exam_id', 'exam_timetables', ['exam_id'], unique=False)
    op.create_index('ix_exam_timetables_subject_id', 'exam_timetables', ['subject_id'], unique=False)
    op.create_index('ix_report_cards_student_id', 'report_cards', ['student_id'], unique=False)
    op.create_index('ix_report_cards_exam_id', 'report_cards', ['exam_id'], unique=False)
    op.create_index('ix_marks_conversion_history_rule_id', 'marks_conversion_history', ['rule_id'], unique=False)
    op.create_index('ix_marks_conversion_rules_verified_by_id', 'marks_conversion_rules', ['verified_by_id'], unique=False)
    op.create_index('ix_marks_conversion_rules_created_by_id', 'marks_conversion_rules', ['created_by_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_users_role_id', table_name='users')
    op.drop_index('ix_admins_user_id', table_name='admins')
    op.drop_index('ix_teachers_user_id', table_name='teachers')
    op.drop_index('ix_teachers_department_id', table_name='teachers')
    op.drop_index('ix_parents_user_id', table_name='parents')
    op.drop_index('ix_students_user_id', table_name='students')
    op.drop_index('ix_students_class_id', table_name='students')
    op.drop_index('ix_parent_students_parent_id', table_name='parent_students')
    op.drop_index('ix_parent_students_student_id', table_name='parent_students')
    op.drop_index('ix_classes_class_teacher_id', table_name='classes')
    op.drop_index('ix_subjects_department_id', table_name='subjects')
    op.drop_index('ix_class_subjects_class_id', table_name='class_subjects')
    op.drop_index('ix_class_subjects_subject_id', table_name='class_subjects')
    op.drop_index('ix_teacher_subjects_teacher_id', table_name='teacher_subjects')
    op.drop_index('ix_teacher_subjects_subject_id', table_name='teacher_subjects')
    op.drop_index('ix_teacher_subjects_class_id', table_name='teacher_subjects')
    op.drop_index('ix_timetables_class_id', table_name='timetables')
    op.drop_index('ix_timetables_subject_id', table_name='timetables')
    op.drop_index('ix_timetables_teacher_id', table_name='timetables')
    op.drop_index('ix_attendance_student_id', table_name='attendance')
    op.drop_index('ix_attendance_class_id', table_name='attendance')
    op.drop_index('ix_attendance_subject_id', table_name='attendance')
    op.drop_index('ix_attendance_teacher_id', table_name='attendance')
    op.drop_index('ix_attendance_marked_by', table_name='attendance')
    op.drop_index('ix_exams_class_id', table_name='exams')
    op.drop_index('ix_exam_invigilators_exam_id', table_name='exam_invigilators')
    op.drop_index('ix_exam_invigilators_teacher_id', table_name='exam_invigilators')
    op.drop_index('ix_exam_results_exam_id', table_name='exam_results')
    op.drop_index('ix_exam_results_student_id', table_name='exam_results')
    op.drop_index('ix_exam_results_subject_id', table_name='exam_results')
    op.drop_index('ix_exam_results_entered_by', table_name='exam_results')
    op.drop_index('ix_exam_subjects_exam_id', table_name='exam_subjects')
    op.drop_index('ix_exam_subjects_subject_id', table_name='exam_subjects')
    op.drop_index('ix_exam_timetables_exam_id', table_name='exam_timetables')
    op.drop_index('ix_exam_timetables_subject_id', table_name='exam_timetables')
    op.drop_index('ix_report_cards_student_id', table_name='report_cards')
    op.drop_index('ix_report_cards_exam_id', table_name='report_cards')
    op.drop_index('ix_marks_conversion_history_rule_id', table_name='marks_conversion_history')
    op.drop_index('ix_marks_conversion_rules_verified_by_id', table_name='marks_conversion_rules')
    op.drop_index('ix_marks_conversion_rules_created_by_id', table_name='marks_conversion_rules')
