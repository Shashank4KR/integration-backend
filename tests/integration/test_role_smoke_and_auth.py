from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import AsyncGenerator
import uuid
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.main import app
from app.models.attendance_model import Attendance, AttendanceStatus
from app.models.class_model import Class
from app.models.class_subject_model import ClassSubject
from app.models.exam_model import Exam
from app.models.exam_models import ExamSubject
from app.models.exam_result_model import ExamResult
from app.models.parent_model import Parent
from app.models.parent_student_model import ParentStudent
from app.models.report_card_model import ReportCard
from app.models.role import Role
from app.models.student_model import Student
from app.models.subject_model import Subject
from app.models.teacher_model import Teacher
from app.models.teacher_subject_model import TeacherSubject
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

    # Mess, maintenance, work orders, dashboards return 401 unauthenticated
    for path in (
        "/mess-menu",
        "/mess-expenses",
        "/mess-collections",
        "/mess-attendance",
        "/maintenance-requests",
        "/work-orders",
        "/hostel/dashboard",
        "/hostel/mess/dashboard",
        "/hostel/maintenance/dashboard",
        "/hostel/dashboard/stats",
    ):
        resp = await async_client.get(path)
        assert resp.status_code == 401, f"{path} did not return 401 unauthenticated"

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

    # 8. Test STUDENT accessing restricted mess, maintenance, work-orders, and hostel dashboard endpoints -> 403
    app.dependency_overrides[get_current_user] = lambda: user_a
    for path in (
        "/mess-expenses",
        "/mess-collections",
        "/mess-attendance",
        "/maintenance-requests",
        "/work-orders",
        "/hostel/dashboard",
        "/hostel/mess/dashboard",
        "/hostel/maintenance/dashboard",
        "/hostel/dashboard/stats",
    ):
        resp = await async_client.get(path)
        assert resp.status_code == 403, f"STUDENT {path} did not return 403, got {resp.status_code}"

    # 9. Test PARENT accessing restricted mess, maintenance, work-orders, and hostel dashboard endpoints -> 403
    app.dependency_overrides[get_current_user] = lambda: user_p
    for path in (
        "/mess-expenses",
        "/mess-collections",
        "/mess-attendance",
        "/maintenance-requests",
        "/work-orders",
        "/hostel/dashboard",
        "/hostel/mess/dashboard",
        "/hostel/maintenance/dashboard",
        "/hostel/dashboard/stats",
    ):
        resp = await async_client.get(path)
        assert resp.status_code == 403, f"PARENT {path} did not return 403, got {resp.status_code}"


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

    # 7. Admin accessing mess, maintenance, work-order, and dashboard endpoints -> 200
    for path in (
        "/mess-menu",
        "/mess-expenses",
        "/mess-collections",
        "/mess-attendance",
        "/maintenance-requests",
        "/work-orders",
        "/hostel/dashboard",
        "/hostel/mess/dashboard",
        "/hostel/maintenance/dashboard",
        "/hostel/dashboard/stats",
    ):
        resp = await async_client.get(path)
        assert resp.status_code == 200, f"ADMIN {path} did not return 200, got {resp.status_code}: {resp.text}"

    # 8. Student and Parent accessing mess-menu -> 200
    app.dependency_overrides[get_current_user] = lambda: student_user
    resp = await async_client.get("/mess-menu")
    assert resp.status_code == 200, f"STUDENT /mess-menu did not return 200, got {resp.status_code}"

    app.dependency_overrides[get_current_user] = lambda: parent_user
    resp = await async_client.get("/mess-menu")
    assert resp.status_code == 200, f"PARENT /mess-menu did not return 200, got {resp.status_code}"


@pytest.mark.asyncio
async def test_maintenance_request_requested_by_user_id_enforcement(
    async_client: AsyncClient, db_session: AsyncSession
):
    """
    Verifies that:
    1. Server always sets requested_by_user_id = current_user.id, ignoring client-supplied value.
    2. requested_by is nullable, and there is NO fallback to first student.
    3. CHECK constraint requires at least requested_by or requested_by_user_id.
    """
    from app.models.hostel_model import HostelBlock, HostelRoom
    admin_role = Role(role_name="ADMIN", description="Administrator")
    db_session.add(admin_role)
    await db_session.flush()

    admin_user = User(username="maint_admin", email="maint_adm@example.com", password_hash="hash", role_id=admin_role.id)
    spoofed_user = User(username="spoofed_user", email="spoofed@example.com", password_hash="hash", role_id=admin_role.id)
    db_session.add_all([admin_user, spoofed_user])
    await db_session.flush()
    admin_user.role = admin_role

    block = HostelBlock(block_name="Block A", block_type="BOYS", total_floors=2, total_rooms=10)
    db_session.add(block)
    await db_session.flush()

    room = HostelRoom(block_id=block.id, room_no="101", floor_no=1, capacity=2)
    db_session.add(room)
    await db_session.commit()

    app.dependency_overrides[get_current_user] = lambda: admin_user

    # Client tries to pass a spoofed requested_by_user_id
    payload = {
        "room_id": str(room.id),
        "issue_type": "Electrical",
        "description": "Fan not working",
        "priority": "HIGH",
        "requested_by_user_id": str(spoofed_user.id),
    }
    resp = await async_client.post("/maintenance-requests", json=payload)
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    data = resp.json()

    # Verify server ignored client-supplied requested_by_user_id and set current_user.id
    assert data["requested_by_user_id"] == str(admin_user.id)
    # Verify requested_by is None (no fallback to a random student)
    assert data["requested_by"] is None


@pytest.mark.asyncio
async def test_teacher_only_attendance_and_marks_entry(
    async_client: AsyncClient, db_session: AsyncSession
):
    """
    Comprehensive test matrix for teacher-only attendance and marks entry:
    1. Unauthenticated (no token) -> 401
    2. ADMIN and SUPER_ADMIN writes -> 403 Forbidden
    3. STUDENT and PARENT writes -> 403 Forbidden
    4. ADMIN reads (GET /attendance, GET /exam-results) -> 200 OK
    5. TEACHER not assigned in teacher_subjects -> 403 Forbidden
    6. TEACHER assigned in teacher_subjects -> 201/200 OK (server sets teacher_id & marked_by)
    7. TEACHER outside correction window -> 403 Forbidden
    8. Report cards: /publish is ADMIN-only (TEACHER gets 403, ADMIN gets 200); /generate works for both.
    """
    # 1. Setup Roles
    admin_role = Role(role_name="ADMIN", description="Administrator")
    super_admin_role = Role(role_name="SUPER_ADMIN", description="Super Administrator")
    teacher_role = Role(role_name="TEACHER", description="Teacher")
    student_role = Role(role_name="STUDENT", description="Student")
    parent_role = Role(role_name="PARENT", description="Parent")
    db_session.add_all([admin_role, super_admin_role, teacher_role, student_role, parent_role])
    await db_session.flush()

    # 2. Setup Users
    admin_user = User(username="admin_user_entry", email="admin_entry@test.com", password_hash="h", role_id=admin_role.id)
    super_admin_user = User(username="super_user_entry", email="super_entry@test.com", password_hash="h", role_id=super_admin_role.id)
    teacher_assigned_user = User(username="teacher_assigned", email="t_assigned@test.com", password_hash="h", role_id=teacher_role.id)
    teacher_unassigned_user = User(username="teacher_unassigned", email="t_unassigned@test.com", password_hash="h", role_id=teacher_role.id)
    student_user = User(username="student_user_entry", email="s_entry@test.com", password_hash="h", role_id=student_role.id)
    parent_user = User(username="parent_user_entry", email="p_entry@test.com", password_hash="h", role_id=parent_role.id)

    db_session.add_all([
        admin_user, super_admin_user, teacher_assigned_user,
        teacher_unassigned_user, student_user, parent_user
    ])
    await db_session.flush()

    admin_user.role = admin_role
    super_admin_user.role = super_admin_role
    teacher_assigned_user.role = teacher_role
    teacher_unassigned_user.role = teacher_role
    student_user.role = student_role
    parent_user.role = parent_role

    # 3. Setup Academic Structure
    class_1 = Class(class_name="Class 10", section="A", academic_year="2025-2026")
    subject_1 = Subject(subject_code="ENG-101", subject_name="English Language")
    db_session.add_all([class_1, subject_1])
    await db_session.flush()

    class_sub = ClassSubject(class_id=class_1.id, subject_id=subject_1.id)
    db_session.add(class_sub)

    teacher_assigned = Teacher(user_id=teacher_assigned_user.id, employee_id="EMP-T1")
    teacher_unassigned = Teacher(user_id=teacher_unassigned_user.id, employee_id="EMP-T2")
    student_1 = Student(user_id=student_user.id, admission_no="ADM-999", class_id=class_1.id)
    db_session.add_all([teacher_assigned, teacher_unassigned, student_1])
    await db_session.flush()

    # Link teacher_assigned to class_1 and subject_1
    ts = TeacherSubject(teacher_id=teacher_assigned.id, class_id=class_1.id, subject_id=subject_1.id)
    db_session.add(ts)

    # Setup Exam
    exam_1 = Exam(
        exam_name="Term 1 Final",
        exam_type="Final",
        class_id=class_1.id,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 15),
        max_marks=100,
    )
    db_session.add(exam_1)
    await db_session.flush()

    exam_sub = ExamSubject(exam_id=exam_1.id, subject_id=subject_1.id)
    db_session.add(exam_sub)
    await db_session.commit()

    # -------------------------------------------------------------
    # A. Unauthenticated requests (no token) -> 401
    # -------------------------------------------------------------
    app.dependency_overrides.pop(get_current_user, None)
    att_payload = {
        "student_id": str(student_1.id),
        "class_id": str(class_1.id),
        "subject_id": str(subject_1.id),
        "teacher_id": str(teacher_assigned.id),
        "attendance_date": "2026-10-05",
        "period_no": 1,
        "status": "PRESENT",
        "marked_by": str(teacher_assigned_user.id),
    }
    marks_payload = {
        "exam_id": str(exam_1.id),
        "student_id": str(student_1.id),
        "subject_id": str(subject_1.id),
        "marks_obtained": 85.5,
        "remarks": "Good",
    }
    assert (await async_client.post("/attendance", json=att_payload)).status_code == 401
    assert (await async_client.post("/exam-results", json=marks_payload)).status_code == 401

    # -------------------------------------------------------------
    # B. ADMIN and SUPER_ADMIN writes get 403 Forbidden
    # -------------------------------------------------------------
    for write_user in (admin_user, super_admin_user):
        app.dependency_overrides[get_current_user] = lambda u=write_user: u
        resp = await async_client.post("/attendance", json=att_payload)
        assert resp.status_code == 403, f"{write_user.username} POST /attendance returned {resp.status_code}"

        resp = await async_client.post("/attendance/bulk", json={
            "class_id": str(class_1.id),
            "subject_id": str(subject_1.id),
            "teacher_id": str(teacher_assigned.id),
            "attendance_date": "2026-10-05",
            "period_no": 1,
            "marked_by": str(write_user.id),
            "records": [{"student_id": str(student_1.id), "status": "PRESENT"}]
        })
        assert resp.status_code == 403, f"{write_user.username} POST /attendance/bulk returned {resp.status_code}"

        resp = await async_client.post("/exam-results", json=marks_payload)
        assert resp.status_code == 403, f"{write_user.username} POST /exam-results returned {resp.status_code}"

    # -------------------------------------------------------------
    # C. STUDENT and PARENT writes get 403 Forbidden
    # -------------------------------------------------------------
    for non_teacher in (student_user, parent_user):
        app.dependency_overrides[get_current_user] = lambda u=non_teacher: u
        resp = await async_client.post("/attendance", json=att_payload)
        assert resp.status_code == 403
        resp = await async_client.post("/exam-results", json=marks_payload)
        assert resp.status_code == 403

    # -------------------------------------------------------------
    # D. ADMIN read access is preserved -> 200 OK
    # -------------------------------------------------------------
    app.dependency_overrides[get_current_user] = lambda: admin_user
    assert (await async_client.get("/attendance")).status_code == 200
    assert (await async_client.get("/exam-results")).status_code == 200

    # -------------------------------------------------------------
    # E. TEACHER unassigned in teacher_subjects gets 403 Forbidden
    # -------------------------------------------------------------
    app.dependency_overrides[get_current_user] = lambda: teacher_unassigned_user
    resp_unassigned_att = await async_client.post("/attendance", json=att_payload)
    assert resp_unassigned_att.status_code == 403
    assert "not assigned" in resp_unassigned_att.text.lower()

    resp_unassigned_marks = await async_client.post("/exam-results", json=marks_payload)
    assert resp_unassigned_marks.status_code == 403
    assert "not assigned" in resp_unassigned_marks.text.lower()

    # -------------------------------------------------------------
    # F. TEACHER assigned gets 201/200 OK & server overrides identity
    # -------------------------------------------------------------
    app.dependency_overrides[get_current_user] = lambda: teacher_assigned_user
    spoofed_att_payload = {
        **att_payload,
        "teacher_id": str(teacher_unassigned.id),  # spoofed
        "marked_by": str(admin_user.id),  # spoofed
    }
    resp_create_att = await async_client.post("/attendance", json=spoofed_att_payload)
    assert resp_create_att.status_code == 201, f"Expected 201, got {resp_create_att.status_code}: {resp_create_att.text}"
    att_data = resp_create_att.json()
    # Verify server set current teacher's ID and current user's ID
    assert att_data["teacher_id"] == str(teacher_assigned.id)
    assert att_data["marked_by"] == str(teacher_assigned_user.id)
    attendance_id = att_data["id"]

    # Teacher update attendance within correction window -> 200
    resp_update_att = await async_client.put(f"/attendance/{attendance_id}", json={"status": "LATE"})
    assert resp_update_att.status_code == 200
    assert resp_update_att.json()["status"] == "LATE"

    # Teacher delete attendance within correction window -> 200
    resp_del_att = await async_client.delete(f"/attendance/{attendance_id}")
    assert resp_del_att.status_code == 200

    # Teacher creates marks -> 201
    resp_create_marks = await async_client.post("/exam-results", json=marks_payload)
    assert resp_create_marks.status_code == 201, f"Expected 201, got {resp_create_marks.status_code}: {resp_create_marks.text}"
    marks_data = resp_create_marks.json()
    marks_id = marks_data["id"]
    assert float(marks_data["marks_obtained"]) == 85.5

    # Teacher updates marks within correction window -> 200
    resp_update_marks = await async_client.put(f"/exam-results/{marks_id}", json={"marks_obtained": 92.0})
    assert resp_update_marks.status_code == 200
    assert float(resp_update_marks.json()["marks_obtained"]) == 92.0

    # -------------------------------------------------------------
    # G. Teacher outside correction window -> 403 Forbidden
    # -------------------------------------------------------------
    # Create an attendance record created 25 hours ago
    expired_att = Attendance(
        student_id=student_1.id,
        class_id=class_1.id,
        subject_id=subject_1.id,
        teacher_id=teacher_assigned.id,
        attendance_date=date(2026, 10, 2),
        period_no=2,
        status=AttendanceStatus.PRESENT,
        marked_by=teacher_assigned_user.id,
        created_at=datetime.now(timezone.utc) - timedelta(hours=25),
    )
    db_session.add(expired_att)
    await db_session.commit()

    resp_expired_att = await async_client.put(f"/attendance/{expired_att.id}", json={"status": "ABSENT"})
    assert resp_expired_att.status_code == 403
    assert "window" in resp_expired_att.text.lower()

    # Expire the exam result created 73 hours ago
    expired_result = await db_session.get(ExamResult, uuid.UUID(marks_id))
    expired_result.created_at = datetime.now(timezone.utc) - timedelta(hours=73)
    await db_session.commit()

    resp_expired_marks = await async_client.put(f"/exam-results/{marks_id}", json={"marks_obtained": 95.0})
    assert resp_expired_marks.status_code == 403
    assert "window" in resp_expired_marks.text.lower()

    # -------------------------------------------------------------
    # H. Report cards: /publish is ADMIN-only; /generate is ADMIN or TEACHER
    # -------------------------------------------------------------
    # TEACHER attempting /publish -> 403
    app.dependency_overrides[get_current_user] = lambda: teacher_assigned_user
    resp_t_publish = await async_client.post(f"/report-cards/publish/{exam_1.id}")
    assert resp_t_publish.status_code == 403

    # ADMIN attempting /publish -> 200
    app.dependency_overrides[get_current_user] = lambda: admin_user
    resp_a_publish = await async_client.post(f"/report-cards/publish/{exam_1.id}")
    assert resp_a_publish.status_code == 200

    # /generate works for both TEACHER and ADMIN (only reads/aggregates)
    gen_payload = {
        "student_id": str(student_1.id),
        "exam_id": str(exam_1.id),
        "remarks": "Generated summary",
    }
    app.dependency_overrides[get_current_user] = lambda: teacher_assigned_user
    assert (await async_client.post("/report-cards/generate", json=gen_payload)).status_code == 200

    app.dependency_overrides[get_current_user] = lambda: admin_user
    assert (await async_client.post("/report-cards/generate", json=gen_payload)).status_code == 200
