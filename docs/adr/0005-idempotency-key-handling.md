# ADR 0005: Idempotency Key Handling on Financial Mutations

## Status
Accepted

## Context
Network timeouts and automatic client retries on payment recording (`POST /payments`, `POST /finance/payments`) and bulk salary disbursements (`POST /finance/salary/bulk-process`) could cause double-charging students or duplicate salary disbursements to faculty.

## Decision
1. Implemented `IdempotencyRecord` table storing:
   - `idempotency_key` (indexed unique string)
   - `request_path` and `request_method`
   - `request_hash` (SHA-256 hash of normalized JSON payload)
   - `status` (`PROCESSING`, `COMPLETED`, `FAILED`)
   - `response_status_code` and `response_json`
   - `created_at` and `expires_at` (24-hour expiration)
2. Support `Idempotency-Key` and `X-Idempotency-Key` headers on financial endpoints.
3. If a request is received with an in-flight key, return `HTTP 409 Conflict` to prevent concurrent execution.
4. If a request matches a previously completed key and payload, replay the cached response with `X-Cache: HIT` and `Idempotent-Replayed: true` headers without re-executing business logic.
5. If the payload differs from the original request under the same key, reject with `HTTP 422 Unprocessable Entity`.

## Consequences
- Prevents catastrophic duplicate payments and double-payroll execution during network instability.
- In-memory/DB lock ensures concurrency safety across distributed requests.
- Requires callers to supply unique UUIDs as idempotency keys on retryable mutations.
