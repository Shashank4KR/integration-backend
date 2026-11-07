import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.main import app
from app.models.role import Role
from app.models.user import User
from app.services.auth_service import AuthService


@pytest.fixture(autouse=True)
def reset_rate_limit():
    from app.core.rate_limit import RateLimitMiddleware
    cur = getattr(app, "middleware_stack", None)
    while cur:
        if isinstance(cur, RateLimitMiddleware):
            with cur._lock:
                cur._requests.clear()
        cur = getattr(cur, "app", None)
    yield


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.clear()


async def _create_user(db_session: AsyncSession, raw_pwd="SecurePassword123"):
    role_res = await db_session.execute(select(Role).where(Role.role_name == "ADMIN"))
    role = role_res.scalar_one_or_none()
    if not role:
        role = Role(id=uuid.uuid4(), role_name="ADMIN", description="Administrator")
        db_session.add(role)
        await db_session.flush()

    user = User(
        id=uuid.uuid4(),
        username=f"session_user_{uuid.uuid4().hex[:6]}",
        email=f"session_{uuid.uuid4().hex[:6]}@example.com",
        password_hash=AuthService.hash_password(raw_pwd),
        role_id=role.id,
        status=True,
        token_version=1,
    )
    user.role = role
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user, raw_pwd


@pytest.mark.asyncio
async def test_access_token_ttl_is_15_minutes():
    """Verify default access token expiration TTL is configured to 15 minutes."""
    assert AuthService.ACCESS_TOKEN_EXPIRE_MINUTES == 15
    token = AuthService.create_access_token({"sub": "test_user"})
    payload = AuthService.verify_token(token)
    assert payload is not None
    assert "exp" in payload
    assert "iat" in payload
    ttl_seconds = payload["exp"] - payload["iat"]
    assert ttl_seconds == 15 * 60


@pytest.mark.asyncio
async def test_login_returns_access_and_refresh_tokens(async_client: AsyncClient, db_session: AsyncSession):
    user, raw_pwd = await _create_user(db_session)
    resp = await async_client.post(
        "/auth/login",
        data={"username": user.username, "password": raw_pwd},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_token_rotation_flow(async_client: AsyncClient, db_session: AsyncSession):
    user, raw_pwd = await _create_user(db_session)
    login_resp = await async_client.post(
        "/auth/login",
        data={"username": user.username, "password": raw_pwd},
    )
    assert login_resp.status_code == 200
    tokens = login_resp.json()
    initial_refresh = tokens["refresh_token"]

    # Call /auth/refresh with initial refresh token
    refresh_resp = await async_client.post(
        "/auth/refresh",
        json={"refresh_token": initial_refresh},
    )
    assert refresh_resp.status_code == 200, refresh_resp.text
    refreshed_data = refresh_resp.json()
    new_access = refreshed_data["access_token"]
    new_refresh = refreshed_data["refresh_token"]

    assert new_access != tokens["access_token"]
    assert new_refresh != initial_refresh

    # New access token is valid
    me_resp = await async_client.get("/auth/me", headers={"Authorization": f"Bearer {new_access}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["id"] == str(user.id)


@pytest.mark.asyncio
async def test_refresh_token_reuse_detection_revokes_sessions(async_client: AsyncClient, db_session: AsyncSession):
    user, raw_pwd = await _create_user(db_session)
    login_resp = await async_client.post(
        "/auth/login",
        data={"username": user.username, "password": raw_pwd},
    )
    initial_refresh = login_resp.json()["refresh_token"]

    # First refresh succeeds
    first_refresh = await async_client.post(
        "/auth/refresh",
        json={"refresh_token": initial_refresh},
    )
    assert first_refresh.status_code == 200
    active_access = first_refresh.json()["access_token"]

    # Attacker tries to reuse initial (now-revoked) refresh token
    reuse_resp = await async_client.post(
        "/auth/refresh",
        json={"refresh_token": initial_refresh},
    )
    assert reuse_resp.status_code == 401
    assert "reuse" in reuse_resp.text.lower()

    # Due to reuse detection, active access token is now invalidated!
    me_resp = await async_client.get("/auth/me", headers={"Authorization": f"Bearer {active_access}"})
    assert me_resp.status_code == 401


@pytest.mark.asyncio
async def test_logout_invalidates_access_token(async_client: AsyncClient, db_session: AsyncSession):
    user, raw_pwd = await _create_user(db_session)
    login_resp = await async_client.post(
        "/auth/login",
        data={"username": user.username, "password": raw_pwd},
    )
    token = login_resp.json()["access_token"]

    # Verify access token works initially
    assert (await async_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})).status_code == 200

    # Logout
    logout_resp = await async_client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logout_resp.status_code == 200

    # Token is immediately rejected after logout
    assert (await async_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})).status_code == 401


@pytest.mark.asyncio
async def test_password_change_invalidates_existing_tokens(async_client: AsyncClient, db_session: AsyncSession):
    user, raw_pwd = await _create_user(db_session)
    login_resp = await async_client.post(
        "/auth/login",
        data={"username": user.username, "password": raw_pwd},
    )
    token = login_resp.json()["access_token"]

    # Change password
    ch_resp = await async_client.post(
        "/auth/change-password",
        json={"current_password": raw_pwd, "new_password": "BrandNewPassword456"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert ch_resp.status_code == 200

    # Old token is immediately rejected
    assert (await async_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})).status_code == 401
