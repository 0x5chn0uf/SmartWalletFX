# Authentication API Reference

> **Audience**: Claude Code and API developers
> **Purpose**: Complete reference for authentication endpoints implemented with singleton pattern

## Register – `POST /auth/register`

Create a new user account with email verification workflow.

**Implementation**: `Auth.register_user()` in `app/api/endpoints/auth.py`

### Request Body (application/json)

Uses the `UserCreate` schema defined in `app/domain/schemas/user.py`:

```json
{
  "username": "alice",
  "email": "alice@example.com",
  "password": "Str0ng!pwd"
}
```

**Schema Validation**:
- **username** – String, 3-50 characters, unique, no spaces
- **email** – Valid email address, unique, normalized
- **password** – 8-100 characters, validated by `PasswordHasher` utility

### Success Response – 201 Created

Returns `UserRead` schema from `app/domain/schemas/user.py`:

```json
{
  "id": "f7b1c1f8-19e4-45b3-b383-4f0d3e28f8a0",
  "username": "alice",
  "email": "alice@example.com",
  "is_active": true,
  "is_verified": false,
  "created_at": "2025-06-18T12:34:56.789Z",
  "updated_at": "2025-06-18T12:34:56.789Z"
}
```

**Note**: `id` is a UUID, `is_verified` starts as `false` until email verification

### Error Responses

All errors follow the `ErrorResponse` schema with trace IDs:

| Status | Condition | Response |
|--------|-----------|----------|
| 409 Conflict | Username/email exists | `{"detail": "username already exists", "code": "CONFLICT", "status_code": 409, "trace_id": "..."}` |
| 400 Bad Request | Weak password | `{"detail": "Password does not meet strength requirements", "code": "BAD_REQUEST", "status_code": 400, "trace_id": "..."}` |
| 422 Validation Error | Invalid payload | Standard FastAPI validation error with trace ID |

### Implementation Notes

- Passwords hashed using `PasswordHasher` utility with bcrypt
- Email verification token sent via `EmailService` 
- Comprehensive audit logging with `Audit.info()` and `Audit.error()`
- Rate limiting not applied to registration (only login)
- Client IP extracted for audit trail: `request.client.host`

### Curl Example

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"Str0ng!pwd"}'
```

---

## Login – `POST /auth/token`

OAuth2 Password Grant flow returning JWT access and refresh tokens.

**Implementation**: `Auth.login_for_access_token()` using singleton pattern with rate limiting.

### Request Body (application/x-www-form-urlencoded)

Uses FastAPI's `OAuth2PasswordRequestForm`:

```
username=alice&password=Str0ng!pwd&grant_type=password
```

### Success Response – 200 OK

Returns `TokenResponse` schema:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 900,
  "refresh_token": "<jwt_refresh>"
}
```

**Cookies**: Both tokens are also set as HTTP-only cookies:
- `access_token` cookie (no path restriction)
- `refresh_token` cookie (path restricted to `/auth`)

### Error Responses

| Status | Condition | Response |
|--------|-----------|----------|
| 401 Unauthorized | Invalid credentials | `{"detail": "Invalid username or password", "code": "AUTH_FAILURE", "status_code": 401, "trace_id": "..."}` |
| 403 Forbidden | Inactive user | `{"detail": "Inactive or disabled user account", "code": "AUTH_FAILURE", "status_code": 403, "trace_id": "..."}` |
| 403 Forbidden | Unverified email | `{"detail": "Email address not verified", "code": "AUTH_FAILURE", "status_code": 403, "trace_id": "..."}` |
| 429 Too Many Requests | Rate limit exceeded | `{"detail": "Too many login attempts, please try again later.", "code": "RATE_LIMIT", "status_code": 429, "trace_id": "..."}` |

### Rate Limiting

**Implementation**: Uses `RateLimiterUtils.login_rate_limiter`:
- Window: 60 seconds
- Max attempts: 5 per client IP
- Reset on successful login
- In-memory implementation (use Redis for production)

### Curl Example

```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice&password=Str0ng!pwd"
```

---

## Token Refresh – `POST /auth/refresh`

Refresh access tokens using refresh JWT.

**Implementation**: `Auth.refresh_access_token()` with multiple token sources.

### Request Options

1. **JSON Body**: `{"refresh_token": "<jwt>"}`
2. **Cookie**: Automatically extracted from `refresh_token` cookie
3. **Authorization Header**: `Authorization: Bearer <refresh_jwt>`

### Success Response – 200 OK

Returns new `TokenResponse` with updated tokens and cookies.

### Error Response

| Status | Condition | Response |
|--------|-----------|----------|
| 401 Unauthorized | Invalid/missing refresh token | Standard error response with trace ID |

### Curl Example

```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<refresh_jwt>"}'
```

---

## Logout – `POST /auth/logout`

Revoke refresh token and clear cookies.

**Implementation**: `Auth.logout()` 

### Behavior
- Clears `access_token` and `refresh_token` cookies
- Revokes refresh token via `AuthUsecase.revoke_refresh_token()`
- Returns 200 OK with no content
- Requires refresh token in cookie

### Error Response

| Status | Condition | Response |
|--------|-----------|----------|
| 401 Unauthorized | Missing refresh token | Standard error response with trace ID |

### Curl Example

```bash
curl -X POST http://localhost:8000/auth/logout \
  -H "Cookie: refresh_token=<refresh_jwt>"
```

---

## Authentication Dependencies

### User Context Extraction

Protected endpoints use `get_user_id_from_request(request)` from `app/api/dependencies`:

```python
from app.api.dependencies import get_user_id_from_request

@staticmethod
@ep.post("/protected-endpoint")
async def protected_operation(request: Request):
    user_id = get_user_id_from_request(request)
    # user_id is UUID of authenticated user
```

### JWT Token Details

**Claims Structure** (managed by `JWTUtils`):
- `sub`: User ID (UUID string)
- `iat`: Issued at timestamp  
- `exp`: Expiration timestamp
- `jti`: JWT ID for tracking
- `type`: "access" or "refresh"

**Token Lifetimes**:
- Access tokens: 15 minutes
- Refresh tokens: 7 days

**Signing**: RS256 with rotating keys (see JWKS endpoint)

---

## Protected Endpoint Example

```python
# Endpoint implementation pattern
class ExampleEndpoint:
    ep = APIRouter(prefix="/example", tags=["example"])
    _usecase: ExampleUsecase
    
    @staticmethod
    @ep.get("/protected")
    async def protected_operation(request: Request):
        user_id = get_user_id_from_request(request)
        return await ExampleEndpoint._usecase.operation(user_id)
```

```bash
# Usage example
curl http://localhost:8000/example/protected \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

---

## Key Security Features

### Timing Attack Mitigation

The login endpoint performs dummy bcrypt verification for non-existent users to prevent user enumeration via response timing analysis.

### Comprehensive Audit Logging

All authentication events are logged with:
- Client IP address
- Username/email attempted
- Success/failure status
- Duration metrics
- Trace IDs for correlation

### Domain Exception Handling

Authentication logic uses domain exceptions:
- `InvalidCredentialsError`
- `InactiveUserError` 
- `UnverifiedEmailError`
- `DuplicateError`

These are caught in endpoints and converted to appropriate HTTP responses.

---

## API Integration Examples

### Complete Login Flow

```bash
# 1. Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"Str0ng!pwd"}'

# 2. Login to get tokens
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice&password=Str0ng!pwd"

# 3. Use access token for protected endpoints
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# 4. Refresh tokens when needed
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"$REFRESH_TOKEN"}'

# 5. Logout to revoke tokens
curl -X POST http://localhost:8000/auth/logout \
  -H "Cookie: refresh_token=$REFRESH_TOKEN"
```

---

## Related Endpoints

- **User Management**: See `app/api/endpoints/users.py` for user profile operations
- **Email Verification**: See `app/api/endpoints/email_verification.py` for email verification flow  
- **Password Reset**: See `app/api/endpoints/password_reset.py` for password reset functionality
- **OAuth**: See `app/api/endpoints/oauth.py` for third-party authentication
- **JWKS**: See `app/api/endpoints/jwks.py` for public key discovery

---

## Implementation Architecture

### Singleton Pattern

The `Auth` class uses the singleton pattern:

```python
class Auth:
    ep = APIRouter(prefix="/auth", tags=["auth"])
    _auth_usecase: AuthUsecase
    _rate_limiter_utils: RateLimiterUtils
    
    def __init__(self, auth_usecase: AuthUsecase, rate_limiter_utils: RateLimiterUtils):
        Auth._auth_usecase = auth_usecase
        Auth._rate_limiter_utils = rate_limiter_utils
    
    @staticmethod
    @ep.post("/register")
    async def register_user(...):
        # Implementation using Auth._auth_usecase
```

### Dependency Injection

Registered in `DIContainer._initialize_endpoints()`:

```python
auth_usecase = self.get_usecase("auth")
rate_limiter_utils = self.get_utility("rate_limiter_utils")
auth_endpoint = Auth(auth_usecase, rate_limiter_utils)
self.register_endpoint("auth", auth_endpoint)
```

---

*This document covers the authentication endpoints implemented in the current codebase. For implementation patterns, see [API_PATTERNS.md](API_PATTERNS.md). For error handling details, see [ERROR_HANDLING.md](ERROR_HANDLING.md).*

*Last updated: 2025-07-19*