import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.v1.transport import transport_router


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_transport_router_has_required_routes():
    routes = [route.path for route in transport_router.routes if hasattr(route, "path")]
    assert "/overview" in routes
    assert "/vehicles" in routes
    assert "/routes" in routes
    assert "/drivers" in routes
    assert "/summary" in routes
    assert "/trips" in routes
    assert "/student-transport" in routes


def test_app_imports_successfully():
    assert app is not None
    assert app.title is not None


def test_finance_router_has_required_routes():
    from app.api.v1.finance import finance_router

    routes = [route.path for route in finance_router.routes if hasattr(route, "path")]
    assert "/overview" in routes
    assert "/transactions" in routes
    assert "/expenses" in routes
    assert "/salary" in routes
    assert "/fee-structures" in routes
    assert "/invoices" in routes
