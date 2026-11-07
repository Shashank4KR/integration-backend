# ADR 0002: Unified API Response Envelope

## Status
Accepted

## Context
Prior to remediation, backend endpoints returned inconsistent shapes: some returned bare JSON lists `[...]`, others returned plain dictionaries `{ "id": ... }`, while errors varied between FastAPI's `{ "detail": ... }` and custom shapes. This caused fragile frontend parsing and prevented universal metadata tracking (e.g. distributed request IDs, ISO timestamps).

## Decision
All public JSON responses will conform to a unified envelope schema:
```json
{
  "success": true,
  "data": <payload>,
  "error": null,
  "meta": {
    "timestamp": "2026-11-07T10:15:17.210737+00:00",
    "requestId": "4769bf13-1f6c-4f6c-a92e-dd661129730b"
  }
}
```
For errors (`4xx` and `5xx`):
```json
{
  "success": false,
  "data": null,
  "error": {
    "message": "Human readable error message",
    "code": 401,
    "details": []
  },
  "meta": {
    "timestamp": "...",
    "requestId": "..."
  }
}
```
Exemptions:
- Raw binary file streaming (e.g. chapter notes PDF/image downloads)
- Documentation endpoints (`/docs`, `/redoc`, `/openapi.json`)
- Health probes (`/health`, `/ready`) returning raw `{"status": "ok"}` for container/load balancer health checks.

## Consequences
- Uniform client parsing across frontend applications.
- Universal correlation between backend server logs and client-side error notifications via `X-Request-ID`.
- Breaking change for external clients expecting bare arrays (mitigated by backward-compatible proxy unwrap logic and root dictionary key preservation).
