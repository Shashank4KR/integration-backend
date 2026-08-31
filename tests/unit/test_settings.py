import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.settings_service import settings_service


@pytest.mark.asyncio
async def test_get_all_settings_returns_defaults(db_session: AsyncSession):
    all_settings = await settings_service.get_all_settings(db_session)
    assert "organization" in all_settings
    assert "academics" in all_settings
    assert "attendance" in all_settings
    assert "examination" in all_settings
    assert "library" in all_settings
    assert "hostel" in all_settings
    assert "transport" in all_settings
    assert "finance" in all_settings
    assert "communication" in all_settings
    assert "roles" in all_settings
    assert "reports" in all_settings
    assert "integrations" in all_settings
    assert "system" in all_settings
    assert "appearance" in all_settings
    assert "notifications" in all_settings
    assert "security" in all_settings
    assert all_settings["organization"]["school_name"] == "Cognora Global Academy"


@pytest.mark.asyncio
async def test_update_category_settings(db_session: AsyncSession):
    updated = await settings_service.update_category_settings(
        db_session,
        "organization",
        {"school_name": "Updated Academy", "school_code": "UA-999"},
    )
    assert updated.category == "organization"
    assert updated.config["school_name"] == "Updated Academy"
    assert updated.config["school_code"] == "UA-999"

    cat = await settings_service.get_category_settings(db_session, "organization")
    assert cat["school_name"] == "Updated Academy"
    assert cat["school_code"] == "UA-999"
    # Fallback keys still preserved
    assert "contact_email" in cat


@pytest.mark.asyncio
async def test_bulk_update_settings(db_session: AsyncSession):
    result = await settings_service.bulk_update_settings(
        db_session,
        {
            "system": {"maintenance_mode": True, "session_timeout_minutes": 120},
            "appearance": {"theme": "Dark"},
        },
    )
    assert result["system"]["maintenance_mode"] is True
    assert result["system"]["session_timeout_minutes"] == 120
    assert result["appearance"]["theme"] == "Dark"
