import json
import logging

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.logging import JSONFormatter, get_request_id, request_id_ctx_var
from app.main import app


def test_json_formatter_structure_and_masking():
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="User login attempt",
        args=(),
        exc_info=None,
    )
    # Add context and sensitive data
    token = request_id_ctx_var.set("req-test-123")
    try:
        record.user_id = "user-uuid"
        record.password = "SuperSecretPassword123"
        record.auth_token = "ey...secret"
        record.safe_meta = {"action": "login"}

        formatted = formatter.format(record)
        data = json.loads(formatted)

        assert data["level"] == "INFO"
        assert data["logger"] == "test_logger"
        assert data["message"] == "User login attempt"
        assert data["request_id"] == "req-test-123"
        assert data["user_id"] == "user-uuid"
        assert data["password"] == "***REDACTED***"
        assert data["auth_token"] == "***REDACTED***"
        assert data["safe_meta"]["action"] == "login"
        assert "timestamp" in data
    finally:
        request_id_ctx_var.reset(token)


@pytest.mark.asyncio
async def test_request_id_middleware_injects_and_preserves_header():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Case 1: Client provides X-Request-ID
        resp = await client.get("/health", headers={"X-Request-ID": "custom-uuid-456"})
        assert resp.status_code == 200
        assert resp.headers.get("X-Request-ID") == "custom-uuid-456"

        # Case 2: Client does not provide X-Request-ID -> server generates one
        resp_gen = await client.get("/health")
        assert resp_gen.status_code == 200
        gen_id = resp_gen.headers.get("X-Request-ID")
        assert gen_id is not None
        assert len(gen_id) >= 16
