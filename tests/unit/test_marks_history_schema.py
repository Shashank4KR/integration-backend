from datetime import datetime

import pytest
from sqlalchemy import DateTime

from app.models.marks_converter_model import MarksConversionHistory


def test_marks_conversion_history_has_updated_at_column():
    table = MarksConversionHistory.__table__
    assert "updated_at" in table.columns, "updated_at column must exist on marks_conversion_history"

    col = table.columns["updated_at"]
    assert isinstance(col.type, DateTime), "updated_at must be a DateTime column"
    assert getattr(col.type, "timezone", False) is True, "updated_at must have timezone=True"
    assert col.nullable is False, "updated_at must not be nullable"
    assert col.server_default is not None, "updated_at must define a server_default"
