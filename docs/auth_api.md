# Authentication API

## Register – `POST /auth/register`

Create a new user account. Accepts JSON payload matching `UserCreate` schema and returns the newly created user (without the password hash) on success.

### Request Body (application/json)
```json
{
  "username": "alice",
  "email": "alice@example.com",
  "password": "Str0ng!pwd"
}
```
* **username** – String, 3-50 characters, unique.
* **email** – Valid email address, unique.
* **password** – 8-100 characters, must include at least one digit and one special symbol.

### Success Response – 201 Created
```json
{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "created_at": "2025-06-18T12:34:56.789Z",
  "updated_at": "2025-06-18T12:34:56.789Z"
}
```

### Error Responses
| Status | Condition | Example Payload |
|--------|-----------|-----------------|
| 409 Conflict | `username` or `email` already exists | `{ "detail": "username already exists" }` |
| 422 Unprocessable Entity | Validation error (weak password, invalid email, etc.) | `{ "detail": [ {"loc": ["body", "password"], "msg": "Password must be ≥8 chars and include at least one digit and one special symbol", "type": "value_error"} ] }` |

### Curl Example
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"Str0ng!pwd"}'
```

### Notes
- Passwords are **never** returned or stored in plaintext; they are hashed using bcrypt.
- Error responses use generic messages to avoid user-enumeration leaks.
- Additional endpoints (login, refresh) will be documented in future subtasks.

## Authentication Workflow – OAuth2 Password Flow

The platform follows RFC 6749 OAuth2 Password Grant flow for first-party clients. Tokens are JSON Web Tokens (JWT) signed with RS256 (or HS256 in test).

1. **Obtain Token** – `POST /auth/token` (Subtask 4.8) with form fields `username`, `password`, `grant_type=password` returns:
   ```json
   {
     "access_token": "<jwt>",
     "token_type": "bearer",
     "expires_in": 900,
     "refresh_token": "<jwt_refresh>"
   }
   ```
2. **Authenticate Requests** – Include the access token in the `Authorization` header:
   ```http
   Authorization: Bearer <jwt>
   ```
3. **Protected Endpoints** – Backend dependencies use `OAuth2PasswordBearer` (`oauth2_scheme`) to extract the token and `get_current_user` to resolve the authenticated user. On failure a `401 Unauthorized` is returned with `WWW-Authenticate: Bearer`.
4. **Token Refresh** – `POST /auth/refresh` (future) exchanges a valid refresh token for a new access token.

### JWT Claims
| Claim | Description |
|-------|-------------|
| `sub` | User ID (string) |
| `iat` | Issued-at timestamp (epoch seconds) |
| `exp` | Expiration timestamp |
| `jti` | Unique token identifier (UUID-hex) |
| `scope` | Optional, e.g. `refresh` for refresh tokens |

Access tokens expire after **15 minutes** by default. Refresh tokens expire after **7 days**.

### Error Responses
| Status | Reason | Example Payload |
|--------|--------|-----------------|
| 401 Unauthorized | Invalid username or password | `{ "detail": "Invalid username or password" }` |
| 403 Forbidden | Account exists but `is_active` is `false` | `{ "detail": "Inactive or disabled user account" }` |
| 429 Too Many Requests | Rate-limit exceeded (see Rate Limiting) | `{ "detail": "Too many login attempts, please try again later." }` |

### Example – Fetch current user
```bash
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### Get Current User – `GET /users/me`

Retrieve the currently authenticated user's public profile. This endpoint is secured by the `Bearer` token issued via `/auth/token`.

**Security Requirements**
- `Authorization: Bearer <access_token>` header must contain a valid **access token**.
- On failure, returns `401 Unauthorized` with `WWW-Authenticate: Bearer` header.
- If the account exists but is inactive/disabled, returns `403 Forbidden`.

#### Success Response – 200 OK
`application/json`
```json
{
  "id": "f7b1c1f8-19e4-45b3-b383-4f0d3e28f8a0",
  "username": "alice",
  "email": "alice@example.com",
  "created_at": "2025-06-18T12:34:56.789Z",
  "updated_at": "2025-06-18T12:34:56.789Z"
}
```

*Field Notes*
| Field | Type | Description |
|-------|------|-------------|
| `id` | `uuid` | Unique user ID (UUID v4) |
| `username` | `string` | Public username, unique |
| `email` | `string` | Email address (public for now; may become private) |
| `created_at` | `datetime` | ISO timestamp of account creation |
| `updated_at` | `datetime` | ISO timestamp of last profile update |

#### Error Responses
| Status | Condition | Example Payload |
|--------|-----------|-----------------|
| 401 Unauthorized | Missing / invalid token | `{ "detail": "Not authenticated" }` |
| 403 Forbidden | User account inactive/disabled | `{ "detail": "Inactive or disabled user account" }` |

#### Curl Example
```bash
curl -X GET http://localhost:8000/users/me \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

#### Rate Limiting

`POST /auth/token` is protected by a **sliding-window rate-limiter** to mitigate credential-stuffing and brute-force attacks.

* **Window**: 60 seconds (configurable via `AUTH_RATE_LIMIT_WINDOW_SECONDS`).
* **Attempts**: 5 failed logins allowed per client IP in the window (`AUTH_RATE_LIMIT_ATTEMPTS`).
* **Response**: Once the threshold is exceeded the endpoint responds with **429 Too Many Requests**.

Example error payload:
```json
{
  "detail": "Too many login attempts, please try again later."
}
```

ℹ️ Production deployments should back the rate-limiter with a shared cache (e.g. Redis) so limits apply across all worker instances. The default in-memory implementation is sufficient for local development and CI.

### Curl Example (access & refresh)
```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice&password=Str0ng!pwd" | jq
```

Sample successful response:
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 900,
  "refresh_token": "<jwt_refresh>"
}
```

### Security Considerations – Timing-Attack Mitigation

To prevent user-enumeration via response-time analysis, the backend performs a **dummy bcrypt verification** even when the supplied username/email does not exist. This keeps the total request latency roughly equal for:

1. *Unknown user* attempts
2. *Known user / wrong password* attempts

Implementation details:
• A cached dummy hash (`$2b$...`) is generated once at runtime – this avoids extra cost after the first call.  
• The password supplied by the client is verified against that hash using `passlib`, ensuring a full bcrypt execution path.  
• After the comparison, the service still raises a generic `InvalidCredentialsError`.

This small extra cost (≈ 50–100 ms) significantly reduces the signal attackers can use to enumerate valid accounts.

## Audit Logging

Successful and failed login attempts emit structured **audit log** entries that can be shipped to SIEM/observability stacks:

```jsonc
{
  "id": "13c2a4d7-5af4-4f5b-8a9e-4de7814a9c2e", // unique event id
  "ts": "2025-06-18T14:25:43.123Z",             // ISO timestamp
  "event": "user_login_success",                // or user_login_failure
  "user_id": "42",                              // absent for unknown-user failures
  "jti": "105b87e4…",                           // JWT id for correlation
  "ip": "203.0.113.5"                           // extracted by proxy middleware (future)
}
```

Logs are written via `app.utils.logging.audit()` ensuring a single-line JSON payload for easy parsing, and are retained independently of application logs.

## Standard Error Response Format (Subtask 4.11)
All error responses now follow a consistent envelope defined by the `ErrorResponse` schema:

```jsonc
{
  "detail": "Invalid username or password",  // human-readable summary
  "code": "AUTH_FAILURE",                   // machine-readable code (see table)
  "trace_id": "7f580fb3-4d94-4b95-9d0b-87850c2c7399" // request correlation id
}
```

| Field     | Type   | Description                                                            |
|-----------|--------|------------------------------------------------------------------------|
| `detail`  | string | Short message safe to expose to clients (no internal details)          |
| `code`    | string | Error category (e.g. `AUTH_FAILURE`, `VALIDATION_ERROR`, `SERVER_ERROR`)|
| `trace_id`| string (uuid) | Unique ID attached to every request, mirrored in `X-Trace-Id` header |

### Current Error Codes
| Code               | Scenario                                   | Typical HTTP Status |
|--------------------|--------------------------------------------|---------------------|
| `AUTH_FAILURE`     | Bad credentials, expired/invalid JWT, inactive user | 401 / 403 |
| `VALIDATION_ERROR` | Body/query/path validation failed          | 422 |
| `BAD_REQUEST`      | Semantically invalid request               | 400 |
| `NOT_FOUND`        | Resource not found                         | 404 |
| `ERROR`            | Other handled exception                    | 4xx / 5xx |
| `SERVER_ERROR`     | Unhandled exception                        | 500 |

### Tracing & Debugging
Clients can log the `trace_id` (or read it from the `X-Trace-Id` response header) and pass it to the support team; the backend logs include the same ID, enabling rapid correlation of client-side errors with server-side logs.

Example failed login curl:
```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice&password=wrong" | jq
```
Response:
```json
{
  "detail": "Invalid username or password",
  "code": "AUTH_FAILURE",
  "trace_id": "1b4b4c33-0a1c-4e68-86b6-091b1b0d9a55"
}
```
Remember to include the `X-Trace-Id` header in bug reports:
```http
X-Trace-Id: 1b4b4c33-0a1c-4e68-86b6-091b1b0d9a55
```

## Key Rotation Note (added 2025-06-19)

Tokens issued by the authentication service now include a `kid` header
identifying the signing key.  No client changes are required—verification is
handled server-side.  Operational details: see `docs/auth_key_rotation.md`.

--- 