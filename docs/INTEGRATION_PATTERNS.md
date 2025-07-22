# Integration Patterns

> **Audience**: Claude Code & contributors  
> **Focus**: External system integration patterns and resilience strategies

This document covers patterns for integrating with external systems including blockchain nodes, third-party APIs, and data sources.

## 1. Blockchain Node Integration

### Web3 Provider Pattern

The application uses web3.py for blockchain interactions with a simple connection pattern:

```python
# app/core/config.py
ARBITRUM_RPC_URL: Optional[str] = None
WEB3_PROVIDER_URI: Optional[str] = None

# Example usage in scripts/script_arbitrum_rpc.py
from web3 import Web3

w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC_URL))
try:
    block_number = w3.eth.block_number
    print(f"Connected to Arbitrum! Latest block: {block_number}")
except Exception as e:
    print(f"Failed to connect to Arbitrum RPC: {e}")
    exit(1)
```

### Pattern: Environment-Based Configuration

- Use environment variables for RPC URLs
- Fail fast with clear error messages when connections fail
- Test connectivity during startup with a simple call like `block_number`

## 2. Third-Party API Client Structure

### OAuth Provider Integration

The application demonstrates OAuth integration patterns for Google and GitHub:

```python
# app/services/oauth_service.py
class OAuthService:
    async def authenticate_or_create(
        self, provider: str, account_id: str, email: Optional[str]
    ) -> User:
        # Check existing account
        account = await self.__oauth_account_repo.get_by_provider_account(
            provider, account_id
        )

        if account:
            # Return existing user
            user = await self.__user_repo.get_by_id(account.user_id)
            self.__audit.info("oauth_existing_account", provider=provider)
            return user

        # Create new user and link account
        # ... implementation
```

### Pattern: Provider-Agnostic Service Layer

- Single service handles multiple OAuth providers
- Consistent audit logging for all provider interactions
- Graceful fallback when user linking fails

### Configuration Pattern

```python
# OAuth provider credentials in config
GOOGLE_CLIENT_ID: Optional[str] = None
GOOGLE_CLIENT_SECRET: Optional[str] = None
GITHUB_CLIENT_ID: Optional[str] = None
GITHUB_CLIENT_SECRET: Optional[str] = None
OAUTH_REDIRECT_URI: str = "http://localhost:8000/auth/oauth/{provider}/callback"
```

## 3. Error Handling for External Dependencies

### Centralized Error Handling

```python
# app/core/error_handling.py
class CoreErrorHandling:
    async def http_exception_handler(
        self, request: Request, exc: HTTPException
    ) -> JSONResponse:
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

### Pattern: Structured Error Responses

- Consistent error response format across all endpoints
- Trace ID for request correlation
- Audit logging for all errors
- Error code mapping for client handling

## 4. Retry and Circuit Breaker Patterns

### Rate Limiting Implementation

```python
# app/utils/rate_limiter.py
class InMemoryRateLimiter:
    def allow(self, key: str) -> bool:
        now = time()
        window_start = now - self.window_seconds
        hits = [ts for ts in self._hits[key] if ts >= window_start]
        self._hits[key] = hits  # prune old hits

        if len(hits) >= self.max_attempts:
            return False
        hits.append(now)
        return True
```

### Redis Distributed Locking

```python
# app/utils/redis_lock.py
@asynccontextmanager
async def acquire_lock(
    redis: Redis, lock_name: str, timeout: int
) -> AsyncGenerator[bool, None]:
    lock_key = f"lock:{lock_name}"
    lock_acquired = await redis.set(lock_key, "locked", nx=True, ex=timeout)
    try:
        yield lock_acquired
    finally:
        if lock_acquired:
            await redis.delete(lock_key)
```

### Pattern: Distributed Coordination

- Use Redis for distributed locking in multi-instance deployments
- TTL-based automatic lock expiration
- Graceful cleanup in finally blocks

## 5. External API Configuration

### Email Service Integration

```python
# Email SMTP configuration
SMTP_HOST: str = "localhost"
SMTP_PORT: int = 1025
SMTP_USERNAME: str | None = None
SMTP_PASSWORD: str | None = None
SMTP_USE_TLS: bool = False
SMTP_USE_SSL: bool = False
EMAIL_FROM: str = "no-reply@smartwalletfx.local"
```

### Pattern: Service-Specific Configuration Groups

- Group related configuration fields together
- Provide sensible defaults for development
- Use Optional types for credentials that may not be set

## 6. Monitoring and Observability

### Prometheus Metrics Integration

```python
# Prometheus configuration
PROMETHEUS_ENABLED: bool = True
PROMETHEUS_PORT: int = 9090
PROMETHEUS_HOST: str = "0.0.0.0"
```

### Audit Logging Pattern

```python
# Consistent audit logging across services
self.__audit.info("oauth_user_created", provider=provider, user_id=str(user.id))
self.__audit.error("oauth_link_missing_user", provider=provider, account_id=account_id)
```

## Key Integration Principles

1. **Environment-based Configuration**: All external service credentials and URLs come from environment variables
2. **Fail Fast**: Test connectivity early and provide clear error messages
3. **Consistent Logging**: Use structured audit logging for all external service interactions
4. **Graceful Degradation**: Handle service unavailability without crashing the application
5. **Resource Cleanup**: Always clean up connections and locks in finally blocks
6. **Provider Abstraction**: Design service layers to handle multiple providers uniformly

## Testing External Integrations

- Mock external services in unit tests
- Use dependency injection to swap implementations
- Test error conditions and timeouts explicitly
- Verify retry logic and circuit breaker behavior

---

_Last updated: 19 July 2025_
