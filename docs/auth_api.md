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
| Status | Reason |
|--------|--------|
| 401 Unauthorized | Missing/invalid/expired token |
| 403 Forbidden | Valid token but insufficient scope/role (future RBAC) |

### Example – Fetch current user
```bash
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

--- 