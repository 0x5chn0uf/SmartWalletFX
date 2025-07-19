# API Patterns Guide

> **Audience**: Claude Code and contributors working on FastAPI endpoints
> **Purpose**: Essential patterns for implementing consistent, maintainable API endpoints

## 1. Endpoint Class Structure & Singleton Pattern

### Core Structure

All endpoints follow a singleton class pattern with dependency injection:

```python
from fastapi import APIRouter, Request, HTTPException, status
from app.usecase.example_usecase import ExampleUsecase
from app.utils.logging import Audit

class ExampleEndpoint:
    """Example endpoint using singleton pattern with dependency injection."""

    ep = APIRouter(prefix="/example", tags=["example"])
    _example_usecase: ExampleUsecase

    def __init__(self, example_usecase: ExampleUsecase):
        """Initialize with injected dependencies."""
        ExampleEndpoint._example_usecase = example_usecase

    @staticmethod
    @ep.post("/items", status_code=status.HTTP_201_CREATED)
    async def create_item(request: Request, payload: ItemCreate) -> ItemResponse:
        """Create a new item."""
        # Implementation here
```

### Key Principles

1. **Static router instance**: `ep = APIRouter()` as class attribute
2. **Dependency injection**: Constructor accepts dependencies, stores as class attributes
3. **Static methods**: All endpoint methods are `@staticmethod`
4. **Consistent naming**: Class name matches domain, methods match HTTP verbs

## 2. Error Response Schemas & Status Codes

### Standard Error Response

Use the centralized error schema for consistent error responses:

```python
from app.domain.schemas.error import ErrorResponse

# All endpoints automatically use this via error handling middleware
class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Human-readable error message")
    code: str = Field(..., description="Machine-readable error code")
    status_code: int = Field(..., description="HTTP status code")
    trace_id: str = Field(..., description="Request correlation identifier")
```

### Status Code Conventions

```python
# Success codes
status.HTTP_200_OK          # GET, PUT operations
status.HTTP_201_CREATED     # POST operations
status.HTTP_204_NO_CONTENT  # DELETE operations

# Client error codes
status.HTTP_400_BAD_REQUEST     # Invalid payload/validation
status.HTTP_401_UNAUTHORIZED    # Missing/invalid auth
status.HTTP_403_FORBIDDEN       # Insufficient permissions
status.HTTP_404_NOT_FOUND       # Resource not found
status.HTTP_409_CONFLICT        # Duplicate resource
status.HTTP_429_TOO_MANY_REQUESTS # Rate limiting

# Server error codes
status.HTTP_500_INTERNAL_SERVER_ERROR  # Unhandled exceptions
```

### Error Handling Pattern

```python
try:
    result = await ExampleEndpoint._usecase.operation(payload)

    Audit.info("operation_success", user_id=user_id, result_id=result.id)
    return result

except DomainSpecificError as e:
    Audit.warning("operation_failed_domain_error", error=str(e))
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Domain error: {e.message}"
    ) from e

except Exception as e:
    Audit.error("operation_failed_unexpected", error=str(e), exc_info=True)
    raise  # Let middleware handle generic errors
```

## 3. Authentication & Authorization Patterns

### User Context Extraction

Use the standardized dependency for extracting user context:

```python
from app.api.dependencies import get_user_id_from_request

@staticmethod
@ep.post("/user-specific-resource")
async def create_resource(request: Request, payload: ResourceCreate):
    """Create a user-specific resource."""
    user_id = get_user_id_from_request(request)

    return await ExampleEndpoint._usecase.create_resource(user_id, payload)
```

### Client IP Extraction

Extract client IP for audit logging:

```python
@staticmethod
@ep.post("/endpoint")
async def endpoint_method(request: Request):
    """Endpoint with client IP tracking."""
    client_ip = request.client.host or "unknown"

    Audit.info("operation_started", client_ip=client_ip)
    # ... rest of implementation
```

### Rate Limiting Integration

For endpoints requiring rate limiting:

```python
from app.utils.rate_limiter import RateLimiterUtils

class AuthEndpoint:
    _rate_limiter_utils: RateLimiterUtils

    def __init__(self, rate_limiter_utils: RateLimiterUtils):
        AuthEndpoint._rate_limiter_utils = rate_limiter_utils

    @staticmethod
    @ep.post("/login")
    async def login(request: Request, form_data: OAuth2PasswordRequestForm):
        identifier = request.client.host or "unknown"
        limiter = AuthEndpoint._rate_limiter_utils.login_rate_limiter

        try:
            # Attempt operation
            result = await AuthEndpoint._auth_usecase.authenticate(...)
            limiter.reset(identifier)  # Reset on success
            return result

        except InvalidCredentialsError:
            if not limiter.allow(identifier):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many login attempts, please try again later."
                )
            # Handle auth failure
```

## 4. Request/Response Validation Patterns

### Input Validation

Use Pydantic models for all request payloads:

```python
from pydantic import BaseModel, Field
from typing import Optional

class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: float = Field(..., gt=0)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Example Item",
                    "description": "An example item",
                    "price": 29.99
                }
            ]
        }
    }
```

### Response Models

Always specify response models for consistent API contracts:

```python
@staticmethod
@ep.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: str) -> ItemResponse:
    """Get item by ID."""
    return await ExampleEndpoint._usecase.get_item(item_id)

@staticmethod
@ep.get("/items", response_model=List[ItemResponse])
async def list_items() -> List[ItemResponse]:
    """List all items."""
    return await ExampleEndpoint._usecase.list_items()
```

### Cookie Handling Pattern

For endpoints setting HTTP-only cookies:

```python
from fastapi import Response

@staticmethod
@ep.post("/login", response_model=TokenResponse)
async def login(response: Response, form_data: OAuth2PasswordRequestForm):
    """Login with cookie setting."""
    tokens = await AuthEndpoint._auth_usecase.authenticate(...)

    # Set secure cookies
    response.set_cookie(
        "access_token",
        tokens.access_token,
        httponly=True,
        samesite="lax",
    )
    response.set_cookie(
        "refresh_token",
        tokens.refresh_token,
        httponly=True,
        samesite="lax",
        path="/auth",  # Restrict scope
    )

    return tokens
```

## 5. Audit Logging Integration

### Structured Logging Pattern

All endpoints must include comprehensive audit logging:

```python
from app.utils.logging import Audit
import time

@staticmethod
@ep.post("/items", response_model=ItemResponse)
async def create_item(request: Request, payload: ItemCreate):
    """Create item with full audit logging."""
    start_time = time.time()
    client_ip = request.client.host or "unknown"
    user_id = get_user_id_from_request(request)

    Audit.info(
        "item_creation_started",
        user_id=user_id,
        item_name=payload.name,
        client_ip=client_ip,
    )

    try:
        result = await ExampleEndpoint._usecase.create_item(user_id, payload)

        duration = int((time.time() - start_time) * 1000)
        Audit.info(
            "item_creation_success",
            user_id=user_id,
            item_id=str(result.id),
            item_name=payload.name,
            duration_ms=duration,
        )

        return result

    except Exception as exc:
        duration = int((time.time() - start_time) * 1000)
        Audit.error(
            "item_creation_failed",
            user_id=user_id,
            item_name=payload.name,
            duration_ms=duration,
            error=str(exc),
            exc_info=True,
        )
        raise
```

### Audit Event Naming Convention

- Format: `{domain}_{operation}_{status}`
- Examples: `user_registration_started`, `wallet_creation_success`, `auth_login_failed`
- Include relevant context: `user_id`, `client_ip`, `duration_ms`, error details

## 6. Complete Example: Wallets Endpoint

```python
from typing import List
from fastapi import APIRouter, Request, status
from app.api.dependencies import get_user_id_from_request
from app.domain.schemas.wallet import WalletCreate, WalletResponse
from app.usecase.wallet_usecase import WalletUsecase
from app.utils.logging import Audit
import time

class Wallets:
    """Wallets endpoint using singleton pattern with dependency injection."""

    ep = APIRouter(tags=["wallets"])
    __wallet_uc: WalletUsecase

    def __init__(self, wallet_usecase: WalletUsecase):
        """Initialize with injected dependencies."""
        Wallets.__wallet_uc = wallet_usecase

    @staticmethod
    @ep.post("/wallets", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
    async def create_wallet(request: Request, wallet: WalletCreate):
        """Create a new wallet."""
        start_time = time.time()
        client_ip = request.client.host or "unknown"
        user_id = get_user_id_from_request(request)

        Audit.info(
            "wallet_creation_started",
            user_id=user_id,
            wallet_address=wallet.address,
            client_ip=client_ip,
        )

        try:
            result = await Wallets.__wallet_uc.create_wallet(user_id, wallet)

            duration = int((time.time() - start_time) * 1000)
            Audit.info(
                "wallet_creation_success",
                user_id=user_id,
                wallet_id=str(result.id),
                duration_ms=duration,
            )

            return result

        except Exception as exc:
            duration = int((time.time() - start_time) * 1000)
            Audit.error(
                "wallet_creation_failed",
                user_id=user_id,
                duration_ms=duration,
                error=str(exc),
                exc_info=True,
            )
            raise

    @staticmethod
    @ep.get("/wallets", response_model=List[WalletResponse])
    async def list_wallets(request: Request):
        """List all wallets for the authenticated user."""
        user_id = get_user_id_from_request(request)
        return await Wallets.__wallet_uc.list_wallets(user_id)
```

---

_This document should be your primary reference for implementing FastAPI endpoints that are consistent with the codebase patterns and architectural decisions._
