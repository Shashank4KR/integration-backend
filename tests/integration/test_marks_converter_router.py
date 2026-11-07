import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.main import app
from app.models.role import Role
from app.models.user import User


@pytest_asyncio.fixture
async def authenticated_client(db_session: AsyncSession) -> AsyncGenerator[tuple[AsyncClient, User], None]:
    async def override_get_db():
        yield db_session

    role = Role(role_name="ADMIN", description="Administrator")
    db_session.add(role)
    await db_session.flush()
    user = User(
        username=f"marks_{uuid.uuid4().hex[:8]}",
        email=f"{uuid.uuid4().hex}@test.invalid",
        password_hash="not-used",
        role_id=role.id,
        role=role,
    )
    db_session.add(user)
    await db_session.flush()

    async def override_current_user():
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client, user
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_convert_endpoint_returns_estimate_and_private_history(authenticated_client):
    client, user = authenticated_client
    response = await client.post(
        "/marks-converter/convert",
        json={
            "board_direction": "CBSE_TO_STATE",
            "state": "Karnataka",
            "class_grade": "Class 10",
            "subject": "Mathematics",
            "exam_type": "Annual",
            "academic_year": "2026-2027",
            "marks_obtained": 80,
            "source_max_marks": 100,
            "target_max_marks": 80,
        },
    )

    assert response.status_code == 200
    assert response.json()["target_marks"] == "64.00"
    assert response.json()["is_official"] is False
    assert "estimate" in response.json()["status_note"].lower()
    history = await client.get("/marks-converter/history")
    assert history.status_code == 200
    history_items = history.json().get("data", history.json()) if isinstance(history.json(), dict) else history.json()
    assert len(history_items) == 1
    assert history_items[0]["target_marks"] == "64.00"
    assert user.id is not None


@pytest.mark.asyncio
async def test_verified_board_rule_controls_target_maximum(authenticated_client):
    client, _ = authenticated_client
    rule_response = await client.post(
        "/marks-converter/rules",
        json={
            "board_direction": "STATE_TO_CBSE",
            "state": "Kerala",
            "class_grade": "Class 12",
            "subject": "Physics",
            "exam_type": "Board Examination",
            "academic_year": "2026-2027",
            "source_max_marks": 80,
            "target_max_marks": 100,
            "method": "PROPORTIONAL",
            "source_title": "Board equivalence notice",
            "reference_url": "https://board.example/rules",
            "is_official": True,
            "is_active": True,
        },
    )
    assert rule_response.status_code == 201

    conversion = await client.post(
        "/marks-converter/convert",
        json={
            "board_direction": "STATE_TO_CBSE",
            "state": "Kerala",
            "class_grade": "Class 12",
            "subject": "Physics",
            "exam_type": "Board Examination",
            "academic_year": "2026-2027",
            "marks_obtained": 64,
            "source_max_marks": 80,
            "target_max_marks": 90,
        },
    )

    assert conversion.status_code == 200
    assert conversion.json()["target_marks"] == "80.00"
    assert conversion.json()["target_max_marks"] == "100.00"
    assert conversion.json()["is_official"] is True
    assert conversion.json()["reference_url"] == "https://board.example/rules"

    deactivated = await client.put(
        f"/marks-converter/rules/{rule_response.json()['id']}",
        json={"is_active": False},
    )
    assert deactivated.status_code == 200
    estimated = await client.post(
        "/marks-converter/convert",
        json={
            "board_direction": "STATE_TO_CBSE",
            "state": "Kerala",
            "class_grade": "Class 12",
            "subject": "Physics",
            "exam_type": "Board Examination",
            "academic_year": "2026-2027",
            "marks_obtained": 64,
            "source_max_marks": 80,
            "target_max_marks": 90,
        },
    )
    assert estimated.status_code == 200
    assert estimated.json()["is_official"] is False
    assert estimated.json()["target_marks"] == "72.00"


@pytest.mark.asyncio
async def test_invalid_conversion_inputs_return_validation_error(authenticated_client):
    client, _ = authenticated_client
    response = await client.post(
        "/marks-converter/convert",
        json={
            "board_direction": "CBSE_TO_STATE",
            "state": "Tamil Nadu",
            "class_grade": "Class 10",
            "exam_type": "Annual",
            "academic_year": "2026-2027",
            "marks_obtained": 101,
            "source_max_marks": 100,
            "target_max_marks": 100,
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_only_administrators_can_manage_rules(authenticated_client):
    client, user = authenticated_client
    user.role.role_name = "STUDENT"
    response = await client.get("/marks-converter/rules?include_inactive=true")
    assert response.status_code == 403
