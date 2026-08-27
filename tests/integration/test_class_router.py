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
from app.models.class_model import Class
from app.models.subject_model import Subject
from app.models.class_subject_model import ClassSubject

async def _override_current_user(user: User):
    async def _dependency() -> User:
        return user
    return _dependency

@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncClient:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_class_subjects(async_client: AsyncClient, db_session: AsyncSession):
    # Setup test data
    admin_role = Role(role_name="ADMIN", description="Admin")
    db_session.add(admin_role)
    await db_session.flush()

    admin_user = User(
        username="admin-user",
        email="admin@example.com",
        password_hash="hash",
        role_id=admin_role.id,
    )
    admin_user.role = admin_role
    db_session.add(admin_user)

    test_class = Class(
        class_name="Class 10-A",
        section="A",
        academic_year="2026-2027",
    )
    db_session.add(test_class)
    await db_session.flush()

    test_subject = Subject(
        subject_name="Mathematics",
        subject_code="MATH101",
    )
    db_session.add(test_subject)
    await db_session.flush()

    class_subject = ClassSubject(
        class_id=test_class.id,
        subject_id=test_subject.id,
    )
    db_session.add(class_subject)
    await db_session.flush()

    app.dependency_overrides[get_current_user] = await _override_current_user(admin_user)
    try:
        response = await async_client.get(f"/classes/{test_class.id}/subjects")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["subject_name"] == "Mathematics"
    assert data[0]["id"] == str(test_subject.id)
