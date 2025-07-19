# Error Handling Guide

> **Audience**: Claude Code and contributors working with error handling patterns
> **Purpose**: Comprehensive guide to the standardized error handling system used throughout the FastAPI application

## Overview

The trading bot backend implements a centralized error handling system using FastAPI's global exception handlers. This document explains how errors are structured, processed, and returned to clients, with patterns for consistent error handling across endpoints.

## Table of Contents

1. [Standard Error Response Format](#standard-error-response-format)
2. [Error Codes and Status Codes](#error-codes-and-status-codes)
3. [Exception Handling Architecture](#exception-handling-architecture)
4. [Request Tracing](#request-tracing)
5. [Audit Logging](#audit-logging)
6. [Client-Side Error Handling](#client-side-error-handling)
7. [Testing Error Scenarios](#testing-error-scenarios)
8. [Adding Custom Error Types](#adding-custom-error-types)

## Standard Error Response Format

All API errors follow a consistent JSON structure defined by the `ErrorResponse` schema:

```json
{
  "detail": "Human-readable error message",
  "code": "MACHINE_READABLE_CODE",
  "status_code": 401,
  "trace_id": "7f580fb3-4d94-4b95-9d0b-87850c2c7399"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `detail` | string | Human-readable error message suitable for display to end users |
| `code` | string | Machine-readable error code for programmatic handling |
| `status_code` | integer | HTTP status code |
| `trace_id` | string (UUID) | Unique identifier for the request, used for correlation with server logs |

This format ensures that:

1. Users receive clear, actionable error messages
2. Clients can programmatically handle different error types
3. Support teams can correlate client errors with server logs

## Error Codes and Status Codes

### Standard Error Codes

| Code | Description | Typical Status Codes |
|------|-------------|---------------------|
| `AUTH_FAILURE` | Authentication or authorization failure | 401, 403 |
| `VALIDATION_ERROR` | Request payload validation failed | 422 |
| `BAD_REQUEST` | Invalid request structure or parameters | 400 |
| `NOT_FOUND` | Requested resource doesn't exist | 404 |
| `CONFLICT` | Resource conflict (e.g., duplicate unique field) | 409 |
| `RATE_LIMIT` | Rate limit exceeded | 429 |
| `SERVER_ERROR` | Unhandled server error | 500 |

### Status Code Mapping

The `CoreErrorHandling` service automatically maps HTTP status codes to appropriate error codes:

```python
_CODE_MAP = {
    400: "BAD_REQUEST",
    401: "AUTH_FAILURE",
    403: "AUTH_FAILURE",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMIT",
}
```

## Exception Handling Architecture

### Global Exception Handlers

The `CoreErrorHandling` service provides centralized exception handling through FastAPI's global exception handlers. All handlers follow the same pattern:

1. Extract trace ID from request state
2. Create standardized `ErrorResponse` 
3. Log error with appropriate severity
4. Return JSON response with consistent format

```python
class CoreErrorHandling:
    """Service for handling global exceptions in FastAPI applications."""
    
    def __init__(self, audit: Audit):
        self.audit = audit
    
    def _get_trace_id(self, request: Request) -> str:
        """Get trace ID from request state."""
        return getattr(request.state, "trace_id", "unknown")
    
    async def http_exception_handler(self, request: Request, exc: HTTPException) -> JSONResponse:
        """Handle HTTP exceptions with standardized response format."""
        trace_id = self._get_trace_id(request)
        code = self._CODE_MAP.get(exc.status_code, "ERROR")
        
        payload = ErrorResponse(
            detail=exc.detail,
            code=code,
            status_code=exc.status_code,
            trace_id=trace_id,
        ).model_dump()
        
        self.audit.error("http_exception", **payload)
        return JSONResponse(status_code=exc.status_code, content=payload)
```

### Exception Handler Flow

1. An exception is raised during request processing
2. FastAPI routes the exception to the appropriate handler
3. The handler:
   - Extracts the trace ID from the request
   - Creates a standardized `ErrorResponse`
   - Logs the error with the trace ID
   - Returns the JSON response to the client

### Domain-Specific Exceptions

The codebase uses domain-specific exceptions for business logic errors. These are defined in `app/domain/errors.py`:

```python
# app/domain/errors.py
class InvalidCredentialsError(Exception):
    """Raised when authentication credentials are invalid."""
    pass

class InactiveUserError(Exception):
    """Raised when a user account is inactive or disabled."""
    pass

class UnverifiedEmailError(Exception):
    """Raised when user email is not verified."""
    pass

class DuplicateError(Exception):
    """Raised when attempting to create a resource that already exists."""
    def __init__(self, field: str):
        self.field = field
        super().__init__(f"Duplicate {field}")
```

### Exception Handling in Endpoints

Endpoints should catch domain exceptions and convert them to appropriate HTTP exceptions:

```python
try:
    user = await Auth._auth_usecase.register(payload)
    return user
except DuplicateError as dup:
    Audit.error("User registration failed - duplicate field", duplicate_field=dup.field)
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"{dup.field} already exists",
    ) from dup
except Exception as exc:
    Audit.error("User registration failed", error=str(exc), exc_info=True)
    raise
```

## Request Tracing

### Trace ID Generation

Trace IDs are managed by the middleware system and extracted in error handlers:

```python
def _get_trace_id(self, request: Request) -> str:
    """Get trace ID from request state."""
    return getattr(request.state, "trace_id", "unknown")
```

The trace ID is:
1. Generated by middleware for each request
2. Stored in `request.state.trace_id`
3. Included in all error responses
4. Used for correlation in audit logs
5. Available in response headers for debugging

### Using Trace IDs for Debugging

When a client reports an error:

1. Ask for the `trace_id` from the error response
2. Search server logs for this ID to find all related log entries
3. Reconstruct the complete request flow and error context

## Audit Logging

### Error Audit Trail

The `CoreErrorHandling` service provides structured error logging with appropriate severity levels:

```python
# Different severity levels for different error types

# Error level: Unhandled exceptions, critical failures
self.audit.error("unhandled_exception", trace_id=trace_id, exc_info=exc)

# Warning level: Expected business logic failures
self.audit.warning("db_conflict", **payload)
self.audit.warning("weak_password", **payload)

# Error level: Authentication and authorization failures  
self.audit.error("http_exception", **payload)
```

### Endpoint-Level Error Logging

Endpoints should include comprehensive audit logging for both success and failure scenarios:

```python
@staticmethod
@ep.post("/register")
async def register_user(request: Request, payload: UserCreate):
    client_ip = request.client.host or "unknown"
    
    Audit.info("User registration started", username=payload.username, client_ip=client_ip)
    
    try:
        user = await Auth._auth_usecase.register(payload)
        Audit.info("User registration completed", user_id=user.id, username=user.username)
        return user
    except DuplicateError as dup:
        Audit.error("User registration failed - duplicate", duplicate_field=dup.field)
        raise HTTPException(status_code=409, detail=f"{dup.field} already exists")
    except Exception as exc:
        Audit.error("User registration failed", error=str(exc), exc_info=True)
        raise
```

### Log Severity Levels

The audit logging system uses structured severity levels:

- **Error**: Unhandled exceptions, authentication failures, critical business logic failures
- **Warning**: Expected business conflicts (integrity errors), weak passwords, rate limiting
- **Info**: Successful operations, operation start/completion events

### Audit Event Naming Convention

Use consistent naming for audit events:
- Format: `{domain}_{operation}_{status}`
- Examples: `user_registration_started`, `wallet_creation_failed`, `auth_login_success`
- Include relevant context: `user_id`, `client_ip`, `duration_ms`, error details

## Client-Side Error Handling

### Frontend Error Handling Best Practices

1. **Check for the error envelope**:
   ```typescript
   try {
     const response = await api.post('/auth/token', credentials);
     return response.data;
   } catch (error) {
     if (error.response?.data?.code === 'AUTH_FAILURE') {
       // Handle authentication failure
     } else if (error.response?.data?.trace_id) {
       // Log the trace ID for support
       console.error(`Error [${error.response.data.trace_id}]:`, error.response.data.detail);
     }
     throw error;
   }
   ```

2. **User-friendly error messages**:
   ```typescript
   // Map error codes to user-friendly messages
   const errorMessages = {
     'AUTH_FAILURE': 'Invalid username or password. Please try again.',
     'VALIDATION_ERROR': 'Please check your input and try again.',
     'RATE_LIMIT': 'Too many attempts. Please try again later.',
     // Default message for unexpected errors
     'DEFAULT': 'Something went wrong. Please try again later.'
   };

   // Get appropriate message
   const message = errorMessages[error.response?.data?.code] || errorMessages.DEFAULT;
   ```

3. **Include trace IDs in support requests**:
   ```typescript
   // Support request form
   const SupportForm = ({ error }) => (
     <form>
       <input type="hidden" name="traceId" value={error.trace_id} />
       <textarea name="description" placeholder="Describe what happened..." />
       <button type="submit">Submit</button>
     </form>
   );
   ```

## Testing Error Scenarios

### Backend Testing

Test that endpoints return proper error responses:

```python
async def test_login_invalid_credentials(client):
    response = await client.post(
        "/auth/token",
        data={"username": "invalid", "password": "wrong"}
    )
    
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "AUTH_FAILURE"
    assert "trace_id" in data
    assert data["detail"] == "Invalid username or password"
```

### Frontend Testing

Test that components handle errors correctly:

```typescript
test('displays error message on authentication failure', async () => {
  // Mock API error response
  api.post.mockRejectedValueOnce({
    response: {
      status: 401,
      data: {
        detail: 'Invalid username or password',
        code: 'AUTH_FAILURE',
        status_code: 401,
        trace_id: '123e4567-e89b-12d3-a456-426614174000'
      }
    }
  });
  
  render(<LoginForm />);
  
  // Submit form
  fireEvent.change(screen.getByLabelText('Username'), {
    target: { value: 'testuser' }
  });
  fireEvent.change(screen.getByLabelText('Password'), {
    target: { value: 'password' }
  });
  fireEvent.click(screen.getByText('Login'));
  
  // Check that error is displayed
  await screen.findByText('Invalid username or password');
});
```

## Adding Custom Error Types

### 1. Create a Custom Exception

Domain exceptions should be simple Python exceptions without HTTP details:

```python
# app/domain/errors.py
class InsufficientBalanceError(Exception):
    """Raised when a wallet has insufficient balance for an operation."""
    
    def __init__(self, required=None, available=None):
        self.required = required
        self.available = available
        
        if required and available:
            message = f"Insufficient balance. Required: {required}, Available: {available}"
        else:
            message = "Insufficient balance for this operation"
            
        super().__init__(message)
```

### 2. Add a Custom Exception Handler (Optional)

For special handling, add a custom handler in `CoreErrorHandling`:

```python
# app/core/error_handling.py
async def insufficient_balance_error_handler(
    self, request: Request, exc: InsufficientBalanceError
) -> JSONResponse:
    """Handle insufficient balance errors."""
    trace_id = self._get_trace_id(request)
    payload = ErrorResponse(
        detail=exc.detail,
        code="INSUFFICIENT_BALANCE",
        status_code=exc.status_code,
        trace_id=trace_id,
    ).model_dump()
    self.audit.warning("insufficient_balance", **payload)
    return JSONResponse(status_code=exc.status_code, content=payload)
```

### 3. Register the Handler

Register the handler in `ApplicationFactory.create_app()`:

```python
app.add_exception_handler(
    InsufficientBalanceError,
    error_handling.insufficient_balance_error_handler,
)
```

### 4. Use the Custom Exception

Raise domain exceptions in business logic, handle in endpoints:

```python
# In usecase (business logic)
async def transfer_funds(self, from_wallet_id: str, amount: float):
    wallet = await self.wallet_repo.get_by_id(from_wallet_id)
    if wallet.balance < amount:
        raise InsufficientBalanceError(
            required=amount,
            available=wallet.balance
        )
    # Continue with transfer...

# In endpoint (HTTP layer)
@staticmethod
@ep.post("/transfer")
async def transfer_funds(request: Request, payload: TransferRequest):
    try:
        result = await WalletEndpoint._usecase.transfer_funds(
            payload.from_wallet_id, payload.amount
        )
        return result
    except InsufficientBalanceError as e:
        Audit.warning("Transfer failed - insufficient balance", 
                     required=e.required, available=e.available)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
```

---

*Last updated: 2025-07-19* 