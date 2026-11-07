import uuid
from collections.abc import AsyncGenerator
from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.main import app
from app.models.fee_model import FeeInvoice, FeeStructure, Payment
from app.models.finance_model import Salary
from app.models.idempotency_model import IdempotencyRecord
from app.models.role import Role
from app.models.student_model import Student
from app.models.teacher_model import Teacher
from app.models.user import User


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_payment_idempotency_key_replay(async_client: AsyncClient, db_session: AsyncSession):
    # Setup roles and users
    admin_role = Role(role_name="ADMIN", description="Admin")
    db_session.add(admin_role)
    await db_session.flush()

    admin_user = User(
        username="idemp_admin",
        email="idemp_admin@example.com",
        password_hash="hash",
        role_id=admin_role.id,
        is_active=True,
    )
    admin_user.role = admin_role

    student_user = User(
        username="idemp_student",
        email="idemp_student@example.com",
        password_hash="hash",
        role_id=admin_role.id,
        is_active=True,
    )
    student_user.role = admin_role
    db_session.add_all([admin_user, student_user])
    await db_session.flush()

    student = Student(user_id=student_user.id, admission_no=f"ADM-{uuid.uuid4().hex[:6]}")
    fee_struct = FeeStructure(fee_type="TUITION", amount=Decimal("5000.00"), is_active=True)
    db_session.add_all([student, fee_struct])
    await db_session.flush()

    invoice = FeeInvoice(
        student_id=student.id,
        fee_type_id=fee_struct.id,
        amount=Decimal("5000.00"),
        status="PENDING",
        invoice_date=date.today(),
        due_date=date.today(),
    )
    db_session.add(invoice)
    await db_session.commit()

    app.dependency_overrides[get_current_user] = lambda: admin_user

    idemp_key = f"idemp-pay-{uuid.uuid4()}"
    payload = {
        "invoice_id": str(invoice.id),
        "payment_date": str(date.today()),
        "amount_paid": "1000.00",
        "payment_method": "ONLINE",
    }

    # First request: creates payment
    resp1 = await async_client.post(
        "/payments",
        json=payload,
        headers={"Idempotency-Key": idemp_key},
    )
    assert resp1.status_code == 201
    data1 = resp1.json()
    payment_id = data1["id"]

    # Verify in DB: exactly 1 payment exists
    count = await db_session.scalar(
        select(func.count(Payment.id)).where(Payment.invoice_id == invoice.id)
    )
    assert count == 1

    # Second request: replay with SAME idempotency key
    resp2 = await async_client.post(
        "/payments",
        json=payload,
        headers={"Idempotency-Key": idemp_key},
    )
    assert resp2.status_code == 201
    assert resp2.headers.get("X-Cache") == "HIT"
    assert resp2.headers.get("Idempotent-Replayed") == "true"
    data2 = resp2.json()
    assert data2["id"] == payment_id

    # Verify in DB: still exactly 1 payment exists (not double-charged)
    count_after = await db_session.scalar(
        select(func.count(Payment.id)).where(Payment.invoice_id == invoice.id)
    )
    assert count_after == 1


@pytest.mark.asyncio
async def test_idempotency_conflict_when_in_progress(async_client: AsyncClient, db_session: AsyncSession):
    role = Role(role_name="ADMIN", description="Admin")
    db_session.add(role)
    await db_session.flush()

    user = User(
        username="idemp_conflict_user",
        email="conflict@example.com",
        password_hash="hash",
        role_id=role.id,
        is_active=True,
    )
    user.role = role
    db_session.add(user)
    await db_session.flush()

    key = f"in-flight-key-{uuid.uuid4()}"
    rec = IdempotencyRecord(
        idempotency_key=key,
        user_id=user.id,
        endpoint="POST /payments",
        request_hash="hash",
        status="PROCESSING",
    )
    db_session.add(rec)
    await db_session.commit()

    app.dependency_overrides[get_current_user] = lambda: user

    resp = await async_client.post(
        "/payments",
        json={
            "invoice_id": str(uuid.uuid4()),
            "payment_date": str(date.today()),
            "amount_paid": "500.00",
            "payment_method": "ONLINE",
        },
        headers={"Idempotency-Key": key},
    )
    assert resp.status_code == 409
    assert "process" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_bulk_salary_idempotency_replay(async_client: AsyncClient, db_session: AsyncSession):
    role = Role(role_name="ADMIN", description="Admin")
    db_session.add(role)
    await db_session.flush()

    admin = User(
        username="bulk_admin",
        email="bulk_admin@example.com",
        password_hash="hash",
        role_id=role.id,
        is_active=True,
    )
    admin.role = role

    teacher_user = User(
        username="bulk_teacher",
        email="bulk_teacher@example.com",
        password_hash="hash",
        role_id=role.id,
        is_active=True,
    )
    teacher_user.role = role
    db_session.add_all([admin, teacher_user])
    await db_session.flush()

    teacher = Teacher(user_id=teacher_user.id, employee_id=f"EMP-{uuid.uuid4().hex[:6]}")
    db_session.add(teacher)
    await db_session.commit()

    app.dependency_overrides[get_current_user] = lambda: admin

    bulk_key = f"bulk-salary-{uuid.uuid4()}"
    payload = [
        {
            "employee_name": "Test Teacher",
            "employee_id": str(teacher.employee_id),
            "amount": "50000.00",
            "month": 11,
            "year": 2026,
            "payment_method": "BANK_TRANSFER",
        }
    ]

    # First call: processes salaries
    resp1 = await async_client.post(
        "/finance/salary/bulk-process",
        json=payload,
        headers={"Idempotency-Key": bulk_key},
    )
    assert resp1.status_code == 201
    assert resp1.json()["success"] is True

    # Check count in DB
    count1 = await db_session.scalar(
        select(func.count(Salary.id)).where(Salary.employee_id == teacher.employee_id)
    )
    assert count1 == 1

    # Second call: replay with same key
    resp2 = await async_client.post(
        "/finance/salary/bulk-process",
        json=payload,
        headers={"Idempotency-Key": bulk_key},
    )
    assert resp2.status_code == 201
    assert resp2.headers.get("X-Cache") == "HIT"
    assert resp2.headers.get("Idempotent-Replayed") == "true"

    # Verify no duplicate salaries created
    count2 = await db_session.scalar(
        select(func.count(Salary.id)).where(Salary.employee_id == teacher.employee_id)
    )
    assert count2 == 1
