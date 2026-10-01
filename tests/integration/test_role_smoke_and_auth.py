from typing import AsyncGenerator
import uuid
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.main import app
from app.models.parent_model import Parent
from app.models.parent_student_model import ParentStudent
from app.models.role import Role
from app.models.student_model import Student
from app.models.teacher_model import Teacher
from app.models.transport_model import Bus, Route, StudentTransport
from app.models.user import User


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
async def test_401_unauthenticated_requests(async_client: AsyncClient):
    """Verifies that protected routes return 401 when accessed without token, and public routes return 200."""
    # Protected endpoints must return 401
    resp = await async_client.get("/classes")
    assert resp.status_code == 401

    resp = await async_client.get("/roles")
    assert resp.status_code == 401

    resp = await async_client.get("/routes")
    assert resp.status_code == 401

    resp = await async_client.get(f"/students/{uuid.uuid4()}")
    assert resp.status_code == 401

    # Truly public endpoints must return 200 without authentication
    health_resp = await async_client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json() == {"status": "ok"}

    status_resp = await async_client.get("/settings/public/system-status")
    assert status_resp.status_code == 200


@pytest.mark.asyncio
async def test_403_role_and_ownership_restrictions(
    async_client: AsyncClient, db_session: AsyncSession
):
    """
    Verifies that roles and ownership checks enforce 403 Forbidden:
    - STUDENT accessing another student's record -> 403
    - STUDENT attempting admin-only user creation -> 403
    - PARENT accessing an unlinked child -> 403
    - TEACHER accessing another teacher's timetable -> 403
    """
    # 1. Create Roles
    admin_role = Role(role_name="ADMIN", description="Administrator")
    student_role = Role(role_name="STUDENT", description="Student")
    parent_role = Role(role_name="PARENT", description="Parent")
    teacher_role = Role(role_name="TEACHER", description="Teacher")
    db_session.add_all([admin_role, student_role, parent_role, teacher_role])
    await db_session.flush()

    # 2. Create Users & Profiles for Student A and Student B
    user_a = User(username="student_a", email="a@example.com", password_hash="hash", role_id=student_role.id)
    user_b = User(username="student_b", email="b@example.com", password_hash="hash", role_id=student_role.id)
    user_p = User(username="parent_p", email="p@example.com", password_hash="hash", role_id=parent_role.id)
    user_t = User(username="teacher_t", email="t@example.com", password_hash="hash", role_id=teacher_role.id)
    user_other_t = User(username="teacher_other", email="ot@example.com", password_hash="hash", role_id=teacher_role.id)
    db_session.add_all([user_a, user_b, user_p, user_t, user_other_t])
    await db_session.flush()

    user_a.role = student_role
    user_b.role = student_role
    user_p.role = parent_role
    user_t.role = teacher_role
    user_other_t.role = teacher_role

    student_a = Student(user_id=user_a.id, admission_no="ADM-A")
    student_b = Student(user_id=user_b.id, admission_no="ADM-B")
    parent = Parent(user_id=user_p.id)
    teacher = Teacher(user_id=user_t.id, employee_id="EMP-T1")
    other_teacher = Teacher(user_id=user_other_t.id, employee_id="EMP-T2")
    db_session.add_all([student_a, student_b, parent, teacher, other_teacher])
    await db_session.flush()

    # Link parent P only to Student A
    link = ParentStudent(parent_id=parent.id, student_id=student_a.id, relationship="FATHER")
    db_session.add(link)
    await db_session.commit()

    # 3. Test Student A accessing Student B's profile -> 403
    app.dependency_overrides[get_current_user] = lambda: user_a
    resp = await async_client.get(f"/students/{student_b.id}")
    assert resp.status_code == 403
    err_text = str(resp.json())
    assert "access" in err_text.lower() or "denied" in err_text.lower()

    # 4. Test Student A accessing Student B's transport -> 403
    resp = await async_client.get(f"/students/{student_b.id}/transport")
    assert resp.status_code == 403

    # 5. Test Student A attempting to create user -> 403
    resp = await async_client.post(
        "/users",
        json={"username": "new_user", "email": "new@example.com", "password": "Password123!", "role_id": str(student_role.id)},
    )
    assert resp.status_code == 403

    # 6. Test Parent P accessing unlinked Student B's transport -> 403
    app.dependency_overrides[get_current_user] = lambda: user_p
    resp = await async_client.get(f"/students/{student_b.id}/transport")
    assert resp.status_code == 403

    # 7. Test Teacher T accessing other teacher's messages -> 403
    app.dependency_overrides[get_current_user] = lambda: user_t
    resp = await async_client.get(f"/teachers/teacher/{other_teacher.id}/messages")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_200_authorized_role_and_ownership(
    async_client: AsyncClient, db_session: AsyncSession
):
    """
    Verifies that authorized roles and owners get 200 OK:
    - STUDENT accessing own student profile & transport -> 200
    - STUDENT accessing widened endpoints (routes, fee-structures, roles, permissions) -> 200
    - PARENT accessing linked child's transport -> 200
    - ADMIN accessing any student -> 200
    """
    # 1. Create Roles & Users
    admin_role = Role(role_name="ADMIN", description="Administrator")
    student_role = Role(role_name="STUDENT", description="Student")
    parent_role = Role(role_name="PARENT", description="Parent")
    db_session.add_all([admin_role, student_role, parent_role])
    await db_session.flush()

    admin_user = User(username="admin_user", email="adm@example.com", password_hash="hash", role_id=admin_role.id)
    student_user = User(username="student_user", email="stu@example.com", password_hash="hash", role_id=student_role.id)
    parent_user = User(username="parent_user", email="par@example.com", password_hash="hash", role_id=parent_role.id)
    db_session.add_all([admin_user, student_user, parent_user])
    await db_session.flush()

    admin_user.role = admin_role
    student_user.role = student_role
    parent_user.role = parent_role

    student = Student(user_id=student_user.id, admission_no="ADM-OK")
    parent = Parent(user_id=parent_user.id)
    db_session.add_all([student, parent])
    await db_session.flush()

    link = ParentStudent(parent_id=parent.id, student_id=student.id, relationship="MOTHER")
    db_session.add(link)

    # Create Transport setup for Student
    bus = Bus(bus_number="BUS-101", model="Standard 40", capacity=40)
    route = Route(route_name="Route 1", start_point="North", end_point="Campus")
    db_session.add_all([bus, route])
    await db_session.flush()

    transport_record = StudentTransport(
        student_id=student.id,
        bus_id=bus.id,
        route_id=route.id,
        stop_point="Main Gate",
    )
    db_session.add(transport_record)
    await db_session.commit()

    # 2. Student accessing own record -> 200
    app.dependency_overrides[get_current_user] = lambda: student_user
    resp = await async_client.get(f"/students/{student.id}")
    assert resp.status_code == 200
    assert resp.json()["admission_no"] == "ADM-OK"

    # 3. Student accessing own transport -> 200
    resp = await async_client.get(f"/students/{student.id}/transport")
    assert resp.status_code == 200
    assert resp.json()["stop_point"] == "Main Gate"

    # 4. Student accessing widened endpoints -> 200
    resp = await async_client.get("/routes")
    assert resp.status_code == 200

    resp = await async_client.get("/fee-structures")
    assert resp.status_code == 200

    resp = await async_client.get("/roles")
    assert resp.status_code == 200

    resp = await async_client.get("/permissions")
    assert resp.status_code == 200

    # 5. Parent accessing linked child's transport -> 200
    app.dependency_overrides[get_current_user] = lambda: parent_user
    resp = await async_client.get(f"/students/{student.id}/transport")
    assert resp.status_code == 200
    assert resp.json()["stop_point"] == "Main Gate"

    # 6. Admin accessing any student -> 200
    app.dependency_overrides[get_current_user] = lambda: admin_user
    resp = await async_client.get(f"/students/{student.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(student.id)
