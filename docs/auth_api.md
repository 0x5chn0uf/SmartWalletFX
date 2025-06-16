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