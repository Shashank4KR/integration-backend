import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_response_envelope_structure_on_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Public health check probe remains raw
        health_res = await client.get("/health")
        assert health_res.status_code == 200
        assert health_res.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_response_envelope_structure_on_401_error():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/classes")
        assert res.status_code == 401
        body = res.json()
        
        assert body["success"] is False
        assert body["data"] is None
        assert isinstance(body["error"], dict)
        assert body["error"]["code"] == 401
        assert "message" in body["error"]
        assert "meta" in body
        assert "timestamp" in body["meta"]
        assert "requestId" in body["meta"]
        assert res.headers.get("x-request-id") == body["meta"]["requestId"]


@pytest.mark.asyncio
async def test_response_envelope_structure_on_validation_error():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Send invalid login payload to trigger 422
        res = await client.post("/auth/login", json={"invalid": "payload"})
        assert res.status_code == 422
        body = res.json()
        
        assert body["success"] is False
        assert body["data"] is None
        assert isinstance(body["error"], dict)
        assert body["error"]["code"] == 422
        assert len(body["error"]["details"]) > 0
        assert "meta" in body
        assert "timestamp" in body["meta"]
        assert "requestId" in body["meta"]
