import uuid
from datetime import date
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.main import app
from app.models.attendance_model import Attendance
from app.models.class_model import Class
from app.models.role import Role
from app.models.student_model import Student
from app.models.subject_model import Subject
from app.models.teacher_model import Teacher
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
async def test_attendance_academic_year_filtering(async_client: AsyncClient, db_session: AsyncSession):
    # Setup roles and users
    admin_role = Role(role_name="ADMIN", description="Admin")
    student_role = Role(role_name="STUDENT", description="Student")
    db_session.add_all([admin_role, student_role])
    await db_session.flush()

    admin_user = User(
        username="admin_att_test",
        email="admin_att@cognora.edu",
        password_hash="dummy",
        role_id=admin_role.id,
    )
    student_user = User(
        username="student_att_test",
        email="student_att@cognora.edu",
        password_hash="dummy",
        role_id=student_role.id,
    )
    db_session.add_all([admin_user, student_user])
    await db_session.flush()

    # Create two classes with different academic years
    class_2025 = Class(
        class_name="Grade 10",
        section="A",
        academic_year="2025-2026",
    )
    class_2024 = Class(
        class_name="Grade 9",
        section="B",
        academic_year="2024-2025",
    )
    db_session.add_all([class_2025, class_2024])
    await db_session.flush()

    # Create teacher and subject
    teacher = Teacher(
        user_id=admin_user.id,
        employee_id=f"EMP-{uuid.uuid4().hex[:6]}",
    )
    subject = Subject(
        subject_code=f"SUB-{uuid.uuid4().hex[:6]}",
        subject_name="Mathematics",
    )
    db_session.add_all([teacher, subject])
    await db_session.flush()

    student = Student(
        user_id=student_user.id,
        admission_no=f"ADM-{uuid.uuid4().hex[:6]}",
        first_name="John",
        last_name="Doe",
        class_id=class_2025.id,
    )
    db_session.add(student)
    await db_session.flush()

    att_2025 = Attendance(
        student_id=student.id,
        class_id=class_2025.id,
        subject_id=subject.id,
        teacher_id=teacher.id,
        attendance_date=date(2025, 9, 1),
        period_no=1,
        status="PRESENT",
        marked_by=admin_user.id,
    )
    att_2024 = Attendance(
        student_id=student.id,
        class_id=class_2024.id,
        subject_id=subject.id,
        teacher_id=teacher.id,
        attendance_date=date(2024, 9, 1),
        period_no=1,
        status="ABSENT",
        marked_by=admin_user.id,
    )
    db_session.add_all([att_2025, att_2024])
    await db_session.commit()

    app.dependency_overrides[get_current_user] = lambda: admin_user

    # 1. Fetch attendance with academic_year="2025-2026"
    resp_2025 = await async_client.get("/attendance", params={"academic_year": "2025-2026"})
    assert resp_2025.status_code == 200
    records_2025 = resp_2025.json()
    assert all(r["class_id"] == str(class_2025.id) for r in records_2025)

    # 2. Fetch attendance with academic_year="2024-2025"
    resp_2024 = await async_client.get("/attendance", params={"academic_year": "2024-2025"})
    assert resp_2024.status_code == 200
    records_2024 = resp_2024.json()
    assert all(r["class_id"] == str(class_2024.id) for r in records_2024)

    # 3. Fetch exams list endpoint works cleanly
    exams_resp = await async_client.get("/exams")
    assert exams_resp.status_code == 200
    assert isinstance(exams_resp.json(), list)
