from starlette.testclient import TestClient
from app.main import app


def test_404_error_response_does_not_leak_x_error_header():
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/non-existent-endpoint-404")
    assert resp.status_code == 404
    assert "x-error" not in resp.headers
    assert "X-Error" not in resp.headers


def test_401_error_response_does_not_leak_x_error_header():
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/marks-converter/rules")
    assert resp.status_code == 401
    assert "x-error" not in resp.headers
    assert "X-Error" not in resp.headers


def test_422_validation_error_does_not_leak_x_error_header():
    client = TestClient(app, raise_server_exceptions=False)
    # /auth/login expects form data (username, password); passing empty body triggers 422
    resp = client.post("/auth/login", data={})
    assert resp.status_code == 422
    assert "x-error" not in resp.headers
    assert "X-Error" not in resp.headers
