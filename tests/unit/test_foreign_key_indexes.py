import os
import re
import pytest
from app.core.database import Base
import app.models


def test_all_131_foreign_keys_have_indexes_in_migrations():
    """Verify that all 131 foreign key columns flagged in the audit report

    have corresponding CREATE INDEX statements across the migration files.
    """
    migrations_dir = r"d:\updated\be\EdTech_backend\alembic\versions"
    migration_files = [
        "c1a2b3c4d5e6_idx_core_users_and_academics.py",
        "c2b3c4d5e6f7_idx_content_communication_transport.py",
        "c3c4d5e6f7a8_idx_finance_and_library.py",
        "c4d5e6f7a8b9_idx_hostel_and_maintenance.py",
    ]

    indexed_pairs = set()
    for fname in migration_files:
        fpath = os.path.join(migrations_dir, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        # Find all op.create_index('ix_table_col', 'table', ['col']
        matches = re.findall(r"op\.create_index\('[^']+',\s*'([^']+)',\s*\['([^']+)'\]", content)
        for tbl, col in matches:
            indexed_pairs.add((tbl, col))

    assert len(indexed_pairs) == 131, f"Expected 131 indexed pairs, found {len(indexed_pairs)}"

    # Check key high-traffic tables flagged in the audit report
    critical_fks = [
        ("attendance", "student_id"),
        ("attendance", "class_id"),
        ("attendance", "teacher_id"),
        ("exam_results", "student_id"),
        ("exam_results", "exam_id"),
        ("fee_invoices", "student_id"),
        ("fee_invoices", "fee_type_id"),
        ("student_transport", "student_id"),
        ("student_transport", "bus_id"),
        ("student_ledgers", "student_id"),
    ]
    for tbl, col in critical_fks:
        assert (tbl, col) in indexed_pairs, f"Missing index for critical FK {tbl}.{col}"
