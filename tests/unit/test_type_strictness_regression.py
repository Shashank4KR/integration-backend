from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.v1.auth.routes import get_current_user
from app.main import app
from app.models.role import Role
from app.models.user import User


@pytest.fixture(autouse=True)
def reset_rate_limit():
    from app.core.rate_limit import RateLimitMiddleware
    from app.main import app
    cur = getattr(app, 'middleware_stack', None)
    while cur:
        if isinstance(cur, RateLimitMiddleware):
            with cur._lock:
                cur._requests.clear()
        cur = getattr(cur, 'app', None)
    yield


@pytest.fixture
def mock_admin_user():
    role = Role(id=uuid4(), role_name="ADMIN", description="Admin")
    user = User(
        id=uuid4(),
        username="strict_admin",
        email="admin@test.edu",
        role_id=role.id,
        status=True,
    )
    user.role = role
    return user


@pytest.mark.asyncio
async def test_auth_profile_rejects_extra_fields(mock_admin_user):
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.put(
                "/auth/profile",
                json={"phone": "+1234567890", "extra_injected_field": "exploit"},
            )
            assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
            data = resp.json()
            assert "detail" in data or "message" in data
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_auth_change_password_rejects_extra_fields(mock_admin_user):
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/auth/change-password",
                json={
                    "current_password": "CurrentPassword123",
                    "new_password": "NewSecretPassword123",
                    "privilege_escalation": True,
                },
            )
            assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_auth_change_password_rejects_missing_fields(mock_admin_user):
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/auth/change-password",
                json={},
            )
            assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_bus_create_rejects_extra_fields(mock_admin_user):
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/buses",
                json={
                    "bus_number": "BUS-99",
                    "model": "Ashok Leyland",
                    "capacity": 50,
                    "malicious_extra": "drop table buses",
                },
            )
            assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_bus_create_rejects_invalid_capacity_types_and_ranges(mock_admin_user):
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. Negative capacity
            resp = await client.post(
                "/buses",
                json={"bus_number": "BUS-99", "model": "Ashok Leyland", "capacity": -5},
            )
            assert resp.status_code == 422

            # 2. Zero capacity
            resp = await client.post(
                "/buses",
                json={"bus_number": "BUS-99", "model": "Ashok Leyland", "capacity": 0},
            )
            assert resp.status_code == 422

            # 3. Excessive capacity (> 200)
            resp = await client.post(
                "/buses",
                json={"bus_number": "BUS-99", "model": "Ashok Leyland", "capacity": 5000},
            )
            assert resp.status_code == 422

            # 4. Non-numeric capacity string
            resp = await client.post(
                "/buses",
                json={"bus_number": "BUS-99", "model": "Ashok Leyland", "capacity": "fifty"},
            )
            assert resp.status_code == 422
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_class_create_rejects_extra_fields(mock_admin_user):
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/classes",
                json={
                    "class_name": "Grade 10",
                    "section": "A",
                    "academic_year": "2026-2027",
                    "extra_unrecognized_key": 12345,
                },
            )
            assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_bulk_assign_fee_rejects_non_uuid(mock_admin_user):
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/finance/student-fee-assignments/bulk-assign",
                json={
                    "student_ids": ["not-a-valid-uuid"],
                    "fee_structure_id": str(uuid4()),
                },
            )
            assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_bulk_assign_fee_rejects_extra_fields(mock_admin_user):
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/finance/student-fee-assignments/bulk-assign",
                json={
                    "student_ids": [str(uuid4())],
                    "fee_structure_id": str(uuid4()),
                    "unauthorized_discount": 100,
                },
            )
            assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
