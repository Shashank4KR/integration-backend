import pytest
from fastapi.routing import APIRoute
from app.main import app
from app.api.v1.auth.routes import get_current_user

PUBLIC_ALLOWLIST = {
    ("GET", "/health"),
    ("POST", "/auth/login"),
    ("POST", "/login"),
    ("GET", "/settings/public/system-status"),
}

INTERNAL_DOCS_PATHS = {"/docs", "/redoc", "/openapi.json", "/docs/oauth2-redirect"}


def has_auth(dependant) -> bool:
    if not dependant:
        return False
    if getattr(dependant, "call", None) == get_current_user:
        return True
    for sub in getattr(dependant, "dependencies", []):
        if has_auth(sub):
            return True
    return False


def get_all_routes(router, current_prefix: str = ""):
    results = []
    for r in router.routes:
        if hasattr(r, "include_context"):
            sub_prefix = current_prefix + (r.include_context.prefix or "")
            results.extend(get_all_routes(r.original_router, sub_prefix))
        elif hasattr(r, "routes"):
            sub_prefix = current_prefix + (getattr(r, "prefix", "") or "")
            results.extend(get_all_routes(r, sub_prefix))
        elif isinstance(r, APIRoute):
            results.append((current_prefix + r.path, r))
    return results


def test_route_auth_integrity():
    """
    Integrity test that asserts every single route across the application
    enforces authentication via `get_current_user`, unless it is explicitly
    listed in the public allowlist:
      - GET /health
      - POST /auth/login
      - POST /login
      - GET /settings/public/system-status
    """
    all_routes = get_all_routes(app)
    assert len(all_routes) > 500, f"Expected > 500 routes, found {len(all_routes)}"

    unprotected = []
    for full_path, route in all_routes:
        if full_path in INTERNAL_DOCS_PATHS:
            continue

        for method in route.methods:
            if method in ("OPTIONS", "HEAD"):
                continue

            if (method, full_path) in PUBLIC_ALLOWLIST:
                continue

            auth = has_auth(getattr(route, "dependant", None))
            if not auth and hasattr(route, "dependencies"):
                for d in route.dependencies:
                    if has_auth(d):
                        auth = True
                        break

            if not auth:
                unprotected.append((method, full_path, route.endpoint.__name__))

    assert not unprotected, (
        f"Found {len(unprotected)} unauthenticated endpoint(s) not on the public allowlist:\n"
        + "\n".join(f"  {m} {p} -> {ep}" for m, p, ep in unprotected)
    )
