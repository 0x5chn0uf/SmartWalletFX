# JWT Key Rotation – Operational Playbook

_Last updated: 2025-06-19_

## Overview
JSON Web Token (JWT) key rotation ensures that cryptographic material used to
sign tokens is regularly refreshed without interrupting authenticated
sessions.  This playbook documents how the trading-bot backend performs and
verifies signing-key rotation.

## Configuration
| Setting | Description | Example |
|---------|-------------|---------|
| `JWT_KEYS` | Mapping of `kid` → secret or public key used for verification | `{ "A": "secretA", "B": "secretB" }` |
| `ACTIVE_JWT_KID` | Identifier of the **current** signing key | `"B"` |
| `JWT_ROTATION_GRACE_PERIOD_SECONDS` | Duration that *retired* keys remain trusted | `300` |

All settings live in `app/core/config.py` and can be overridden by ENV vars.

## Rotation Procedure
1. **Generate new secret or RSA key-pair.**  _HS256_ environments require only
a random 256-bit string; _RS256_ requires a 2048-bit RSA key-pair.
2. **Call** `utils.jwt.rotate_signing_key(new_kid, new_secret)` (or equivalent
admin endpoint coming in Task 4.18) which:
   a. Inserts the new key into `JWT_KEYS`.
   b. Sets `ACTIVE_JWT_KID = new_kid` so *new* tokens are signed with it.
   c. Adds the *old* key to an in-memory retired-key map for the configured
grace-period.
3. **Deploy updated configuration** (e.g. ENV vars, Kubernetes secret).  The
application hot-loads the new key without restart.
4. **Monitor audit logs** for `JWT_KEY_ROTATED` event confirming success.

## Grace-Period Behaviour
• Tokens signed with the *previous* key remain valid until the grace-period
expires, after which requests fail with `401 Unauthorized` and audit event
`JWT_OLD_TOKEN_REJECTED`.

• The grace-period should exceed the maximum expected client token TTL plus
clock skew.

## Failure Modes & Mitigation
| Scenario | Result | Mitigation |
|----------|--------|-----------|
| `ACTIVE_JWT_KID` not present in `JWT_KEYS` | Service start-up error | CI linter will fail build; verify config before deploy |
| Key rotated but grace-period too short | Users receive 401 mid-session | Use at least 2× access-token TTL |
| Compromised signing key | Set grace-period to `0`, rotate immediately, and revoke refresh tokens |

## API Impact
Tokens now include a `kid` header specifying the signing key.  Clients **do
not need to change anything**; verification is entirely server-side.

## Testing
Integration and Hypothesis property-based tests cover:
• Dual-key acceptance during grace-period.
• Rejection of retired-key tokens post-grace.
• Signature invariants under random secret generation.

See `backend/tests/integration/auth/test_key_rotation.py` and
`backend/tests/unit/auth/test_jwt_properties.py` for details.

## Future Work
• Admin REST endpoint & Celery cron job to schedule automatic rotations.
• Persist retired-key metadata in Redis to survive pod restarts.
• JWKS endpoint for front-end SPAs and third-party service integration.

---
© 2025 Trading-Bot Platform – Security Engineering 