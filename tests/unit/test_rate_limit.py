from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.rate_limit import RateLimitMiddleware


def test_requests_over_limit_return_429():
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, requests_per_minute=2)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/health").status_code == 200
        limited = client.get("/health")
        assert limited.status_code == 429
        assert limited.headers["X-RateLimit-Remaining"] == "0"


def test_authentication_routes_have_a_stricter_limit():
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, requests_per_minute=20)

    @app.post("/auth/login")
    async def login():
        return {"ok": True}

    with TestClient(app) as client:
        for _ in range(10):
            assert client.post("/auth/login").status_code == 200
        limited = client.post("/auth/login")
        assert limited.status_code == 429
        assert limited.headers["X-RateLimit-Limit"] == "10"


def test_rate_limit_test_isolation_across_runs():
    """Verify that autouse fixture cleanly purges previous bucket allocations between tests."""
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, requests_per_minute=2)

    @app.get("/endpoint")
    async def endpoint():
        return {"status": "ok"}

    # Test that bucket starts completely fresh and allows requests immediately
    with TestClient(app) as client:
        assert client.get("/endpoint").status_code == 200
        assert client.get("/endpoint").status_code == 200
