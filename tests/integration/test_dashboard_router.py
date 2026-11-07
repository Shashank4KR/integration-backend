from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.main import app
from app.models.role import Role
from app.models.student_model import Student
from app.models.teacher_model import Teacher
from app.models.user import User


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
async def test_student_dashboard_rejects_unrelated_student_access(async_client: AsyncClient, db_session: AsyncSession):
    student_role = Role(role_name="STUDENT", description="Student")
    db_session.add(student_role)
    await db_session.flush()

    owner_user = User(
        username="student-owner",
        email="student-owner@example.com",
        password_hash="hash",
        role_id=student_role.id,
    )
    other_user = User(
        username="student-other",
        email="student-other@example.com",
        password_hash="hash",
        role_id=student_role.id,
    )
    db_session.add_all([owner_user, other_user])
    await db_session.flush()

    owner_student = Student(
        user_id=owner_user.id,
        admission_no="ADM-001",
        first_name="Alice",
        last_name="Student",
    )
    other_student = Student(
        user_id=other_user.id,
        admission_no="ADM-002",
        first_name="Bob",
        last_name="Student",
    )
    db_session.add_all([owner_student, other_student])
    await db_session.flush()

    owner_user.role = student_role
    other_user.role = student_role

    app.dependency_overrides[get_current_user] = await _override_current_user(owner_user)
    try:
        response = await async_client.get(f"/dashboard/student/{other_student.id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["message"] == "You do not have permission to access this student's records"


@pytest.mark.asyncio
async def test_teacher_dashboard_rejects_unrelated_teacher_access(async_client: AsyncClient, db_session: AsyncSession):
    teacher_role = Role(role_name="TEACHER", description="Teacher")
    db_session.add(teacher_role)
    await db_session.flush()

    owner_user = User(
        username="teacher-owner",
        email="teacher-owner@example.com",
        password_hash="hash",
        role_id=teacher_role.id,
    )
    other_user = User(
        username="teacher-other",
        email="teacher-other@example.com",
        password_hash="hash",
        role_id=teacher_role.id,
    )
    db_session.add_all([owner_user, other_user])
    await db_session.flush()

    owner_teacher = Teacher(
        user_id=owner_user.id,
        employee_id="EMP-001",
    )
    other_teacher = Teacher(
        user_id=other_user.id,
        employee_id="EMP-002",
    )
    db_session.add_all([owner_teacher, other_teacher])
    await db_session.flush()

    owner_user.role = teacher_role
    other_user.role = teacher_role

    app.dependency_overrides[get_current_user] = await _override_current_user(owner_user)
    try:
        response = await async_client.get(f"/dashboard/teacher/{other_teacher.id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["message"] == "You do not have permission to access this teacher's records"
