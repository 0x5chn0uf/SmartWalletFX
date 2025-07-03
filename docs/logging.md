# Backend Logging Standards

## Overview

This document defines the logging standards and best practices for the backend application. We use structured logging with JSON format for machine readability and consistent parsing.

## Logging Infrastructure

### Current Setup

- **Structured Logging**: Uses `structlog` for JSON-formatted logs
- **Audit Logging**: Dedicated audit logger for security events
- **Configuration**: Centralized in `app/core/logging.py`
- **Context Support**: Trace ID propagation via `structlog.contextvars`

### Log Levels

| Level        | Usage                           | Examples                                                  |
| ------------ | ------------------------------- | --------------------------------------------------------- |
| **DEBUG**    | Detailed diagnostic information | SQL queries, request/response payloads, internal state    |
| **INFO**     | General application flow        | Request start/end, business events, state changes         |
| **WARNING**  | Recoverable issues              | Deprecated features, rate limiting, validation failures   |
| **ERROR**    | Unhandled exceptions            | Database errors, external API failures, unexpected states |
| **CRITICAL** | System-level failures           | Database connection loss, critical service failures       |

## Logging Standards

### 1. Logger Initialization

```python
import logging

logger = logging.getLogger(__name__)
```

### 2. Structured Log Format

All logs should include these standard fields:

```python
# Standard fields
logger.info("User action completed",
    user_id=user.id,
    action="wallet_created",
    wallet_address=wallet.address,
    duration_ms=elapsed_time
)

# Error logging with context
logger.error("Database operation failed",
    operation="wallet_creation",
    user_id=user.id,
    wallet_address=address,
    error=str(exc),
    exc_info=True  # Include stack trace
)
```

### 3. Context Fields

| Field            | Type | Description                           | Example                       |
| ---------------- | ---- | ------------------------------------- | ----------------------------- |
| `user_id`        | UUID | Current user identifier               | `user_id=user.id`             |
| `wallet_address` | str  | Wallet address being operated on      | `wallet_address="0x123..."`   |
| `operation`      | str  | Operation being performed             | `operation="wallet_creation"` |
| `duration_ms`    | int  | Operation duration in milliseconds    | `duration_ms=150`             |
| `trace_id`       | str  | Request trace identifier (auto-added) | `trace_id="abc123"`           |

### 4. Audit Logging

For security-relevant events, use the audit logger:

```python
from app.utils.logging import audit

# Security events
audit("user_login_success", user_id=user.id, ip_address=request.client.host)
audit("wallet_created", user_id=user.id, wallet_address=wallet.address)
audit("permission_denied", user_id=user.id, resource="wallet", action="delete")
```

## Module-Specific Guidelines

### API Endpoints

- Log request start with method, path, and user context
- Log response status and duration
- Log errors with full context

### Use Cases

- Log business operation start/end
- Log important business decisions
- Log validation failures

### Repositories

- Log database operations (create, update, delete)
- Log query performance for slow operations
- Log constraint violations

### Services

- Log external API calls and responses
- Log service state changes
- Log performance metrics

### Tasks (Celery)

- Log task start/end with parameters
- Log task failures with retry information
- Log long-running task progress

## Best Practices

### ✅ Do's

- Use structured logging with key-value pairs
- Include relevant context in every log
- Log at appropriate levels
- Use descriptive event names
- Include timing information for operations
- Log errors with full stack traces

### ❌ Don'ts

- Don't log sensitive data (passwords, tokens, private keys)
- Don't use string formatting for log messages
- Don't log at DEBUG level in production
- Don't log without context
- Don't use print() statements

### Performance Considerations

- Use DEBUG level sparingly in production
- Avoid expensive operations in log statements
- Use lazy evaluation for expensive context

## Examples

### API Endpoint Logging

```python
import logging
import time
from fastapi import Request

logger = logging.getLogger(__name__)

@router.post("/wallets")
async def create_wallet(request: Request, payload: WalletCreate):
    start_time = time.time()
    logger.info("Creating wallet",
        user_id=current_user.id,
        wallet_address=payload.address,
        request_id=request.headers.get("X-Request-ID")
    )

    try:
        result = await wallet_usecase.create_wallet(payload)
        duration = int((time.time() - start_time) * 1000)
        logger.info("Wallet created successfully",
            user_id=current_user.id,
            wallet_address=payload.address,
            duration_ms=duration
        )
        return result
    except Exception as exc:
        duration = int((time.time() - start_time) * 1000)
        logger.error("Wallet creation failed",
            user_id=current_user.id,
            wallet_address=payload.address,
            duration_ms=duration,
            error=str(exc),
            exc_info=True
        )
        raise
```

### Repository Logging

```python
import logging
import time

logger = logging.getLogger(__name__)

async def create(self, address: str, user_id: uuid.UUID, name: str) -> Wallet:
    start_time = time.time()
    logger.debug("Creating wallet in database",
        address=address,
        user_id=user_id,
        name=name
    )

    try:
        db_wallet = Wallet(user_id=user_id, address=address, name=name)
        self.db.add(db_wallet)
        await self.db.commit()
        await self.db.refresh(db_wallet)

        duration = int((time.time() - start_time) * 1000)
        logger.info("Wallet created in database",
            wallet_id=db_wallet.id,
            address=address,
            user_id=user_id,
            duration_ms=duration
        )
        return db_wallet
    except IntegrityError as exc:
        await self.db.rollback()
        duration = int((time.time() - start_time) * 1000)
        logger.warning("Wallet creation failed - duplicate address",
            address=address,
            user_id=user_id,
            duration_ms=duration,
            error=str(exc)
        )
        raise HTTPException(status_code=400, detail="Wallet address already exists")
    except Exception as exc:
        await self.db.rollback()
        duration = int((time.time() - start_time) * 1000)
        logger.error("Database error during wallet creation",
            address=address,
            user_id=user_id,
            duration_ms=duration,
            error=str(exc),
            exc_info=True
        )
        raise
```

## Monitoring and Alerting

### Log Aggregation

- All logs are emitted as JSON to stdout
- External log processors (Loki, Datadog, etc.) can parse structured logs
- Trace ID propagation enables request tracing

### Alerting Thresholds

- ERROR level logs trigger immediate alerts
- WARNING level logs are monitored for patterns
- Performance metrics (duration_ms) are tracked for anomalies

## Testing

### Log Testing

```python
import pytest
import logging
from app.utils.logging import audit

def test_logging_includes_context(caplog):
    caplog.set_level(logging.INFO)

    audit("test_event", user_id="123", action="test")

    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelname == "INFO"
    assert "test_event" in record.message
    assert "user_id" in record.message
```

## Migration Guide

### Adding Logging to Existing Modules

1. **Add logger import**:

   ```python
   import logging
   logger = logging.getLogger(__name__)
   ```

2. **Add request logging** to API endpoints
3. **Add operation logging** to use cases
4. **Add database logging** to repositories
5. **Add service logging** to external integrations
6. **Test logging** with appropriate test fixtures

### Gradual Migration

- Start with critical paths (auth, wallet operations)
- Add logging incrementally to avoid performance impact
- Monitor log volume and adjust levels as needed
