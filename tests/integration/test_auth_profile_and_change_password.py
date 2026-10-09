from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.main import app
from app.models.role import Role
from app.models.user import User
from app.services.auth_service import AuthService


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_profile_success_and_persist(async_client: AsyncClient, db_session: AsyncSession):
    role = Role(role_name="ADMIN", description="Administrator")
    db_session.add(role)
    await db_session.flush()

    user = User(
        username="admin_profile_test",
        email="admin_test@cognora.edu",
        password_hash=AuthService.hash_password("OldPassword123"),
        role_id=role.id,
        avatar_url="https://example.com/old.png",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    app.dependency_overrides[get_current_user] = lambda: user

    # 1. Update avatar and phone
    response = await async_client.put(
        "/auth/profile",
        json={"avatar_url": "data:image/jpeg;base64,/9j/4AAQSkZJRg==", "phone": "+1234567890"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["avatar_url"] == "data:image/jpeg;base64,/9j/4AAQSkZJRg=="
    assert data["phone"] == "+1234567890"

    # 2. Verify /auth/me returns updated avatar
    me_resp = await async_client.get("/auth/me")
    assert me_resp.status_code == 200
    assert me_resp.json()["avatar_url"] == "data:image/jpeg;base64,/9j/4AAQSkZJRg=="

    # 3. Test validation rejection for oversized or invalid avatar
    bad_resp = await async_client.put(
        "/auth/profile",
        json={"avatar_url": "javascript:alert(1)"},
    )
    assert bad_resp.status_code == 400


@pytest.mark.asyncio
async def test_change_password_workflow(async_client: AsyncClient, db_session: AsyncSession):
    role = Role(role_name="TEACHER", description="Teacher")
    db_session.add(role)
    await db_session.flush()

    user = User(
        username="teacher_pwd_test",
        email="teacher_pwd@cognora.edu",
        password_hash=AuthService.hash_password("CurrentPassword123"),
        role_id=role.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    app.dependency_overrides[get_current_user] = lambda: user

    # 1. Wrong current password fails
    bad_res = await async_client.post(
        "/auth/change-password",
        json={"current_password": "WrongPassword", "new_password": "NewSecretPassword123"},
    )
    assert bad_res.status_code == 400
    err_msg = bad_res.json().get("message") or bad_res.json().get("detail") or ""
    assert "Incorrect current password" in err_msg

    # 2. Too short password fails
    short_res = await async_client.post(
        "/auth/change-password",
        json={"current_password": "CurrentPassword123", "new_password": "123"},
    )
    assert short_res.status_code == 400
    err_msg = short_res.json().get("message") or short_res.json().get("detail") or ""
    assert "at least 6 characters" in err_msg

    # 3. Valid change succeeds
    good_res = await async_client.post(
        "/auth/change-password",
        json={"current_password": "CurrentPassword123", "new_password": "NewSecretPassword123"},
    )
    assert good_res.status_code == 200
    assert good_res.json()["message"] == "Password changed successfully"
