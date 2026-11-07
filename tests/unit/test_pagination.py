import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app
from app.models.department_model import Department
from app.models.user import User
from app.models.role import Role
from app.api.v1.auth.routes import get_current_user
from app.repositories.crud_repository import CRUDRepository
from app.services.crud_service import CRUDService


@pytest.mark.asyncio
async def test_crud_repository_pagination_structure_and_limits(db_session: AsyncSession):
    repo = CRUDRepository(Department)
    
    # Create 3 departments for testing
    for i in range(3):
        dept = Department(department_name=f"Paginated Dept {i}")
        db_session.add(dept)
    await db_session.commit()

    # Default pagination
    result = await repo.list(db_session)
    assert isinstance(result, dict)
    assert "items" in result
    assert "total" in result
    assert result["total"] >= 3
    assert len(result["items"]) <= 50

    # Limit parameter
    limited = await repo.list(db_session, limit=2, offset=0)
    assert len(limited["items"]) == 2
    assert limited["total"] >= 3

    # Offset parameter
    offset_res = await repo.list(db_session, limit=2, offset=1)
    assert len(offset_res["items"]) <= 2
    assert offset_res["items"][0].id == limited["items"][1].id

    # Max limit cap at 200: safe_limit clamped
    huge = await repo.list(db_session, limit=500, offset=0)
    assert len(huge["items"]) <= 200


@pytest.mark.asyncio
async def test_router_factory_pagination_endpoints(db_session: AsyncSession):
    # Setup test admin user
    role = Role(role_name="ADMIN", description="Admin Role")
    db_session.add(role)
    await db_session.flush()

    admin_user = User(
        username="pagination_admin",
        email="pag_admin@example.com",
        password_hash="hashed_pw",
        role_id=role.id,
        is_active=True,
    )
    db_session.add(admin_user)
    await db_session.commit()
    await db_session.refresh(admin_user)

    app.dependency_overrides[get_current_user] = lambda: admin_user

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Test GET /departments returns items + total
            resp = await client.get("/departments?limit=10&offset=0")
            assert resp.status_code == 200
            data = resp.json()
            assert "items" in data
            assert "total" in data
            assert isinstance(data["items"], list)
            assert isinstance(data["total"], int)

            # 2. Test query parameter max validation (limit > 200 -> 422)
            resp_invalid_limit = await client.get("/departments?limit=250")
            assert resp_invalid_limit.status_code == 422

            # 3. Test query parameter min validation (limit < 1 -> 422)
            resp_zero_limit = await client.get("/departments?limit=0")
            assert resp_zero_limit.status_code == 422

            # 4. Test query parameter negative offset (offset < 0 -> 422)
            resp_neg_offset = await client.get("/departments?offset=-1")
            assert resp_neg_offset.status_code == 422
    finally:
        app.dependency_overrides.clear()
