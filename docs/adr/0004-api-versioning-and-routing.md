# ADR 0004: API Versioning and Routing Architecture

## Status
Accepted

## Context
FastAPI originally mounted the modular application router directly at the root (`/`), e.g., `/students`, `/auth/login`, etc. The Next.js frontend proxy was configured to strip `/api/v1` to prevent 404 errors. This violated platform standards requiring explicit REST versioning (`/api/v1/...`) and prevented non-breaking future API iterations (`v2`).

## Decision
1. **Explicit Mounting**:
   - `api_router` is explicitly included in `app/main.py` under `prefix="/api/v1"`.
   - OpenAPI schemas and Swagger documentation at `/docs` correctly document `/api/v1/...` routes.
2. **Backward-Compatibility Rewrite**:
   - Added `v1_compatibility_rewrite` HTTP middleware in FastAPI that rewrites incoming un-prefixed requests (e.g. `/students`) to `/api/v1/students` internally.
   - Preserves raw infrastructure paths (`/health`, `/ready`, `/docs`, `/openapi.json`).
3. **Frontend Proxy Synchronization**:
   - Updated Next.js catch-all proxy (`app/api/[...path]/route.ts`) to forward to `${backendUrl}/api/v1/${path}`.

## Consequences
- Clean, versioned REST contracts compliant with industry API standards.
- Zero downtime or breakage for legacy clients and integration tests.
- Clear path for future versioning (`/api/v2`).
