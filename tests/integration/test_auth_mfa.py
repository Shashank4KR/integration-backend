import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.models.role import Role
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.totp_service import TOTPService


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


async def _create_admin_user(db_session: AsyncSession, raw_pwd="SecurePassword123"):
    role_res = await db_session.execute(select(Role).where(Role.role_name == "ADMIN"))
    role = role_res.scalar_one_or_none()
    if not role:
        role = Role(id=uuid.uuid4(), role_name="ADMIN", description="Administrator")
        db_session.add(role)
        await db_session.flush()

    user = User(
        id=uuid.uuid4(),
        username=f"mfa_admin_{uuid.uuid4().hex[:6]}",
        email=f"mfa_{uuid.uuid4().hex[:6]}@example.com",
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
async def test_mfa_setup_enable_disable_lifecycle(async_client: AsyncClient, db_session: AsyncSession):
    user, raw_pwd = await _create_admin_user(db_session)
    login_resp = await async_client.post(
        "/auth/login",
        data={"username": user.username, "password": raw_pwd},
    )
    token = login_resp.json()["access_token"]

    # 1. Setup MFA
    setup_resp = await async_client.post(
        "/auth/mfa/setup",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert setup_resp.status_code == 200, setup_resp.text
    setup_data = setup_resp.json()
    assert "secret" in setup_data
    assert "otpauth_uri" in setup_data
    secret = setup_data["secret"]

    # 2. Bad verification code fails
    bad_enable = await async_client.post(
        "/auth/mfa/enable",
        json={"code": "000000"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert bad_enable.status_code == 400

    # 3. Valid TOTP code enables MFA
    valid_code = TOTPService.generate_totp(secret)
    good_enable = await async_client.post(
        "/auth/mfa/enable",
        json={"code": valid_code},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert good_enable.status_code == 200
    assert "enabled" in good_enable.json()["message"].lower()

    # 4. Disable MFA
    disable_code = TOTPService.generate_totp(secret)
    disable_resp = await async_client.post(
        "/auth/mfa/disable",
        json={"code": disable_code},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert disable_resp.status_code == 200
    assert "disabled" in disable_resp.json()["message"].lower()


@pytest.mark.asyncio
async def test_mfa_login_enforcement_when_flag_enabled(async_client: AsyncClient, db_session: AsyncSession, monkeypatch):
    user, raw_pwd = await _create_admin_user(db_session)
    secret = TOTPService.generate_secret()

    # First login to enable MFA
    login_resp = await async_client.post(
        "/auth/login",
        data={"username": user.username, "password": raw_pwd},
    )
    token = login_resp.json()["access_token"]

    # Set user secret and enable
    user.mfa_secret = secret
    user.mfa_enabled = True
    db_session.add(user)
    await db_session.commit()

    # Turn ON the ENABLE_MFA flag
    monkeypatch.setattr(settings, "ENABLE_MFA", True)

    # Login without MFA header fails
    no_mfa = await async_client.post(
        "/auth/login",
        data={"username": user.username, "password": raw_pwd},
    )
    assert no_mfa.status_code == 401
    assert "mfa" in no_mfa.text.lower()

    # Login with wrong MFA code fails
    wrong_mfa = await async_client.post(
        "/auth/login",
        data={"username": user.username, "password": raw_pwd},
        headers={"X-MFA-Code": "999999"},
    )
    assert wrong_mfa.status_code == 401

    # Login with valid MFA code succeeds
    valid_totp = TOTPService.generate_totp(secret)
    good_mfa = await async_client.post(
        "/auth/login",
        data={"username": user.username, "password": raw_pwd},
        headers={"X-MFA-Code": valid_totp},
    )
    assert good_mfa.status_code == 200
    assert "access_token" in good_mfa.json()
