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
from app.models.academic_content_model import ChapterNote, LessonPlan
from app.models.class_model import Class
from app.models.parent_model import Parent
from app.models.parent_student_model import ParentStudent
from app.models.role import Role
from app.models.student_model import Student
from app.models.subject_model import Subject
from app.models.teacher_model import Teacher
from app.models.teacher_subject_model import TeacherSubject
from app.models.user import User


@pytest_asyncio.fixture
async def secured_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_cross_class_academic_records_are_forbidden(secured_client, db_session, tmp_path, monkeypatch):
    from app.api.v1.academics import academic_content

    monkeypatch.setattr(academic_content, "UPLOAD_DIR", str(tmp_path))
    roles = {name: Role(role_name=name) for name in ("ADMIN", "STUDENT", "PARENT", "TEACHER")}
    db_session.add_all(roles.values())
    await db_session.flush()
    users = {
        key: User(username=f"vapt_{key}_{uuid.uuid4().hex[:6]}", email=f"{uuid.uuid4()}@test", password_hash="x", role_id=roles[role].id)
        for key, role in (("admin", "ADMIN"), ("student", "STUDENT"), ("parent", "PARENT"), ("teacher", "TEACHER"))
    }
    db_session.add_all(users.values())
    await db_session.flush()
    for key, user in users.items():
        user.role = roles["ADMIN" if key == "admin" else key.upper()]
    class_a = Class(class_name="A", section="A", academic_year="2026")
    class_b = Class(class_name="B", section="B", academic_year="2026")
    subject = Subject(subject_code=f"V{uuid.uuid4().hex[:8]}", subject_name="VAPT")
    db_session.add_all([class_a, class_b, subject])
    await db_session.flush()
    student = Student(user_id=users["student"].id, admission_no=f"S{uuid.uuid4().hex[:8]}", class_id=class_a.id)
    parent = Parent(user_id=users["parent"].id)
    teacher = Teacher(user_id=users["teacher"].id, employee_id=f"T{uuid.uuid4().hex[:8]}")
    db_session.add_all([student, parent, teacher])
    await db_session.flush()
    db_session.add_all([
        ParentStudent(parent_id=parent.id, student_id=student.id),
        TeacherSubject(teacher_id=teacher.id, class_id=class_a.id, subject_id=subject.id),
    ])
    other_student = Student(user_id=users["admin"].id, admission_no=f"S{uuid.uuid4().hex[:8]}", class_id=class_b.id)
    db_session.add(other_student)
    await db_session.flush()
    plan = LessonPlan(teacher_id=teacher.id, class_id=class_b.id, subject_id=subject.id, chapter_name="Unit", topic="Topic", plan_date=date.today())
    note = ChapterNote(teacher_id=teacher.id, class_id=class_b.id, subject_id=subject.id, chapter_name="Unit", title="Note", file_url="/api/chapter-notes/files/private.pdf", file_name="private.pdf")
    db_session.add_all([plan, note])
    await db_session.commit()

    for role in ("student", "parent", "teacher"):
        app.dependency_overrides[get_current_user] = lambda key=role: users[key]
        assert (await secured_client.get(f"/classes/{class_b.id}/students")).status_code == 403
        assert (await secured_client.get(f"/lesson-plans?class_id={class_b.id}")).status_code == 403
        assert (await secured_client.get(f"/chapter-notes?class_id={class_b.id}")).status_code == 403
        assert (await secured_client.get("/chapter-notes/files/private.pdf")).status_code == 403
        assert (await secured_client.delete(f"/chapter-notes/{note.id}")).status_code == 403
        assert (await secured_client.put(f"/lesson-plans/{plan.id}", json={"topic": "tampered"})).status_code == 403
        assert (await secured_client.delete(f"/lesson-plans/{plan.id}")).status_code == 403

    app.dependency_overrides[get_current_user] = lambda: users["teacher"]
    html_upload = await secured_client.post(
        "/chapter-notes/upload",
        data={"class_id": str(class_a.id), "subject_id": str(subject.id), "chapter_name": "Unit", "title": "Unsafe"},
        files={"file": ("active.html", b"<script>alert(1)</script>", "text/html")},
    )
    assert html_upload.status_code == 415
    pdf_upload = await secured_client.post(
        "/chapter-notes/upload",
        data={"class_id": str(class_a.id), "subject_id": str(subject.id), "chapter_name": "Unit", "title": "Safe"},
        files={"file": ("handout.pdf", b"%PDF-1.4\ncontent", "application/pdf")},
    )
    assert pdf_upload.status_code == 201
    download = await secured_client.get(pdf_upload.json()["file_url"].replace("/api", "", 1))
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/octet-stream"
    assert download.headers["content-disposition"].startswith("attachment;")
    assert download.headers["x-content-type-options"] == "nosniff"
    monkeypatch.setattr(academic_content, "MAX_NOTE_SIZE", 8)
    oversized = await secured_client.post(
        "/chapter-notes/upload",
        data={"class_id": str(class_a.id), "subject_id": str(subject.id), "chapter_name": "Unit", "title": "Too large"},
        files={"file": ("large.pdf", b"%PDF-1.4\n", "application/pdf")},
    )
    assert oversized.status_code == 413

    app.dependency_overrides[get_current_user] = lambda: users["admin"]
    assert (await secured_client.get(f"/classes/{class_b.id}/students")).status_code == 200
    assert (await secured_client.get(f"/lesson-plans?class_id={class_b.id}")).status_code == 200
    assert (await secured_client.get(f"/chapter-notes?class_id={class_b.id}")).status_code == 200


@pytest.mark.asyncio
async def test_upload_request_body_limit_returns_413(secured_client):
    response = await secured_client.post(
        "/chapter-notes/upload",
        content=b"x" * (11 * 1024 * 1024 + 1),
        headers={"Content-Type": "application/octet-stream"},
    )
    assert response.status_code == 413
