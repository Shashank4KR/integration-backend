# ADR 0003: Session Management, Token Rotation, and Invalidation

## Status
Accepted

## Context
Previously, JWT access tokens had a 60-minute fixed expiration time without refresh token support or server-side revocation. Logging out or changing passwords did not invalidate active tokens, leaving stolen credentials active until natural expiration.

## Decision
1. **Access Token Lifespan**: Reduced access token time-to-live (TTL) to 15 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES: 15`).
2. **Refresh Token Rotation**:
   - Issued refresh tokens with 7-day TTL stored as SHA-256 hashes in a dedicated `refresh_tokens` database table.
   - Calling `POST /api/v1/auth/refresh` immediately revokes the used token and issues a new pair.
   - Reuse of a revoked token triggers automatic revocation of all descendant tokens for that user session family (breach detection).
3. **Instant Token Revocation**:
   - Added `token_version: int` column on `users` table.
   - Embedded `token_version` claim into access token JWTs.
   - `POST /api/v1/auth/logout` and password change operations increment `token_version`, immediately invalidating all outstanding JWTs across all devices.
4. **Multi-Factor Authentication (TOTP)**:
   - Implemented RFC 6238 TOTP behind config toggle `ENABLE_MFA: bool = False` (default off to prevent lockout during migration).

## Consequences
- Significant reduction in exposure window for intercepted tokens.
- True session invalidation on logout and password reset.
- Minimal overhead in authentication middleware via indexed token_version checks.
