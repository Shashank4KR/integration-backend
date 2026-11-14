from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
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
        email="admin_test@nomera.edu",
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
        email="teacher_pwd@nomera.edu",
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
    assert "at least 12 characters" in err_msg

    # 3. Valid change succeeds
    good_res = await async_client.post(
        "/auth/change-password",
        json={"current_password": "CurrentPassword123", "new_password": "NewSecretPassword123"},
    )
    assert good_res.status_code == 200
    assert good_res.json()["message"] == "Password changed successfully"
    await db_session.refresh(user)
    assert AuthService.verify_password("NewSecretPassword123", user.password_hash)
    assert not AuthService.verify_password("CurrentPassword123", user.password_hash)


@pytest.mark.asyncio
async def test_forgot_password_reset_is_single_use_and_does_not_enumerate(
    async_client: AsyncClient, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
):
    from app.core.config import settings

    delivered_links: list[str] = []
    monkeypatch.setattr(settings, "SMTP_HOST", "mail.test")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "noreply@nomera.test")
    monkeypatch.setattr("app.api.v1.auth.routes._send_reset_email", lambda _email, url: delivered_links.append(url))
    role = Role(role_name="ADMIN", description="Administrator")
    db_session.add(role)
    await db_session.flush()
    user = User(
        username="admin_reset_test",
        email="admin_reset@nomera.edu",
        password_hash=AuthService.hash_password("OldPassword12345"),
        role_id=role.id,
    )
    db_session.add(user)
    await db_session.commit()

    found = await async_client.post("/auth/forgot-password", json={"email": user.email})
    missing = await async_client.post("/auth/forgot-password", json={"email": "missing@nomera.edu"})
    assert found.status_code == missing.status_code == 200
    assert found.json()["message"] == missing.json()["message"]
    assert "development_reset_token" not in found.json()
    assert len(delivered_links) == 1
    token = delivered_links[-1].split("#token=", 1)[1]

    reset = await async_client.post("/auth/reset-password", json={
        "token": token, "new_password": "UpdatedPassword123", "confirm_password": "UpdatedPassword123",
    })
    assert reset.status_code == 200
    await db_session.refresh(user)
    assert AuthService.verify_password("UpdatedPassword123", user.password_hash)
    assert not AuthService.verify_password("OldPassword12345", user.password_hash)
    login_new = await async_client.post("/auth/login", data={"username": user.email, "password": "UpdatedPassword123"})
    login_old = await async_client.post("/auth/login", data={"username": user.email, "password": "OldPassword12345"})
    assert login_new.status_code == 200
    assert login_old.status_code == 401

    reused = await async_client.post("/auth/reset-password", json={
        "token": token, "new_password": "AnotherPassword123", "confirm_password": "AnotherPassword123",
    })
    assert reused.status_code == 400

    mismatch = await async_client.post("/auth/reset-password", json={
        "token": token, "new_password": "AnotherPassword123", "confirm_password": "MismatchPassword123",
    })
    assert mismatch.status_code == 400

    from app.models.password_reset import PasswordReset
    second_request = await async_client.post("/auth/forgot-password", json={"email": user.email})
    assert second_request.json()["message"] == found.json()["message"]
    expired_token = delivered_links[-1].split("#token=", 1)[1]
    reset_row = await db_session.scalar(select(PasswordReset).where(PasswordReset.token_hash == AuthService.hash_token(expired_token)))
    reset_row.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    await db_session.commit()
    expired = await async_client.post("/auth/reset-password", json={
        "token": expired_token, "new_password": "AnotherPassword123", "confirm_password": "AnotherPassword123",
    })
    assert expired.status_code == 400
