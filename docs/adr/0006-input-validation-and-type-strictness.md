# ADR 0006: Input Validation, Schema Strictness, and Type Integrity

## Status
Accepted

## Context
Multiple mutation endpoints originally accepted untyped dictionaries (`payload: dict` or `Any`), including profile updates, password changes, system settings, and fee adjustments. Pydantic models lacked `extra="forbid"`, allowing mass-assignment attacks where extra fields were accepted without error. Furthermore, implicit type coercion allowed string `"50"` where integer `50` was expected.

## Decision
1. **Replacement of Untyped DTOs**:
   - Replaced all `dict` / `Any` endpoint parameters with dedicated Pydantic models with explicit field constraints (e.g. `ProfileUpdateRequest`, `PasswordChangeRequest`, `SystemSettingsUpdatePayload`).
2. **Base Schema Configuration**:
   - Created `BaseSchema` with `ConfigDict(extra="forbid")` and inherited across all request DTOs. Any unexpected field now triggers an immediate `HTTP 422 Unprocessable Entity`.
3. **Bound Enforcement**:
   - Enforced strict bounds on numeric inputs (`gt=0, le=100` for bus capacities, `gt=0` for fees, `ge=0, le=1000` for exam marks).
   - Enforced non-empty string constraints (`min_length=1, max_length=100`) on textual identifiers.
4. **Clean 422 vs 500**:
   - Ensured all malformed boundary inputs are intercepted by validation handlers, preventing unhandled 500 internal server errors.

## Consequences
- Total elimination of mass-assignment vulnerabilities.
- Complete type integrity across API input -> validation schema -> model -> DB column.
- Explicit, predictable error responses for client developers.
