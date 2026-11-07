import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_api_v1_endpoints_and_legacy_compatibility():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Both /health and /api/v1/health work
        r_health_root = await client.get("/health")
        assert r_health_root.status_code == 200
        assert r_health_root.json() == {"status": "ok"}

        r_health_v1 = await client.get("/api/v1/health")
        assert r_health_v1.status_code == 200
        assert r_health_v1.json() == {"status": "ok"}

        # Direct /api/v1 route call
        r_v1 = await client.post("/api/v1/auth/login", json={"invalid": "data"})
        assert r_v1.status_code == 422
        assert r_v1.json()["success"] is False

        # Legacy un-prefixed route call (rewritten to /api/v1)
        r_legacy = await client.post("/auth/login", json={"invalid": "data"})
        assert r_legacy.status_code == 422
        assert r_legacy.json()["success"] is False


def test_openapi_schema_uses_api_v1_prefix():
    openapi_schema = app.openapi()
    paths = openapi_schema.get("paths", {})
    
    # Verify modular paths are mounted under /api/v1/
    v1_paths = [p for p in paths.keys() if p.startswith("/api/v1/")]
    assert len(v1_paths) > 200, f"Expected > 200 paths under /api/v1/, found {len(v1_paths)}"
