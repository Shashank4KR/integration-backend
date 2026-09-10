import pytest
from app.api.v1.transport import transport_router


def test_transport_router_has_required_routes():
    routes = [route.path for route in transport_router.routes if hasattr(route, "path")]
    assert "/overview" in routes
    assert "/vehicles" in routes
    assert "/routes" in routes
    assert "/drivers" in routes
    assert "/summary" in routes
    assert "/trips" in routes
    assert "/student-transport" in routes


def test_transport_router_has_driver_assign_route():
    routes = [route.path for route in transport_router.routes if hasattr(route, "path")]
    assert "/drivers/assign" in routes
