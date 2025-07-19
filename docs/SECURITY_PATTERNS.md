# Security Patterns for Claude Code

This document outlines the security patterns and implementations used in the trading bot codebase. These patterns ensure proper authentication, authorization, and data protection.

## JWT Token Rotation Patterns

### Overview

The application implements automated JWT key rotation using a Redis-distributed lock pattern with Celery tasks for scalability and reliability.

### Implementation Pattern

#### 1. Key Rotation State Machine

```python
# Pure functional approach for key rotation decisions
from app.utils.jwt_rotation import promote_and_retire_keys, KeySet

def decide_rotation(current_keys: KeySet, now: datetime) -> KeySetUpdate:
    """Pure function that decides which keys to promote/retire"""
    return promote_and_retire_keys(current_keys, now)
```

#### 2. Distributed Lock Pattern

```python
# Redis-based distributed locking for single-worker execution
@asynccontextmanager
async def acquire_lock(redis: Redis, lock_name: str, timeout: int):
    lock_key = f"lock:{lock_name}"
    lock_acquired = await redis.set(lock_key, "locked", nx=True, ex=timeout)
    try:
        yield lock_acquired
    finally:
        if lock_acquired:
            await redis.delete(lock_key)
```

#### 3. Automated Rotation Task

```python
# Celery task with exponential backoff
@celery.task(bind=True)
def promote_and_retire_keys_task(self):
    async def _run():
        async with acquire_lock(redis, "jwt_key_rotation", timeout=300) as got_lock:
            if not got_lock:
                return  # Another worker is handling rotation

            key_set = _gather_current_key_set()
            update = promote_and_retire_keys(key_set, datetime.now(timezone.utc))
            if not update.is_noop():
                _apply_key_set_update(update)

    try:
        asyncio.run(_run())
    except Exception as exc:
        retry_delay = min(60 * 60, (self.request.retries + 1) * 60)
        raise self.retry(exc=exc, countdown=retry_delay)
```

#### 4. Grace Period Management

```python
# Retired keys remain valid during grace period
_RETIRED_KEYS: dict[str, datetime] = {}

def rotate_signing_key(new_kid: str, new_signing_key: str, config: Configuration):
    old_kid = config.ACTIVE_JWT_KID
    config.JWT_KEYS[new_kid] = new_signing_key
    config.ACTIVE_JWT_KID = new_kid

    if old_kid and old_kid != new_kid:
        retire_at = datetime.now(timezone.utc) + timedelta(
            seconds=config.JWT_ROTATION_GRACE_PERIOD_SECONDS
        )
        _RETIRED_KEYS[old_kid] = retire_at
```

### Key Implementation Rules for Claude Code

1. **Always use distributed locks** for rotation tasks in multi-worker environments
2. **Implement grace periods** to prevent token invalidation during rotation
3. **Use pure functions** for rotation logic to enable reliable testing
4. **Include retry mechanisms** with exponential backoff for transient failures
5. **Invalidate caches** after key rotation to ensure immediate propagation

## RBAC Implementation Details

### Role-Based Access Control Structure

```python
class UserRole(str, Enum):
    ADMIN = "admin"
    TRADER = "trader"
    FUND_MANAGER = "fund_manager"
    INDIVIDUAL_INVESTOR = "individual_investor"

class Permission(str, Enum):
    WALLET_READ = "wallet:read"
    WALLET_WRITE = "wallet:write"
    PORTFOLIO_READ = "portfolio:read"
    DEFI_WRITE = "defi:write"
    ADMIN_SYSTEM = "admin:system"
```

### Permission Mapping Pattern

```python
# Static mapping from roles to permissions
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    UserRole.ADMIN.value: [
        Permission.WALLET_READ.value,
        Permission.WALLET_WRITE.value,
        Permission.ADMIN_SYSTEM.value,
        # ... all permissions
    ],
    UserRole.INDIVIDUAL_INVESTOR.value: [
        Permission.WALLET_READ.value,
        Permission.PORTFOLIO_READ.value,
        # ... read-only permissions
    ]
}
```

### Authorization Helper Functions

```python
def has_permission(user_roles: List[str], required_permission: str) -> bool:
    """Check if user has specific permission based on roles"""
    user_permissions = get_permissions_for_roles(user_roles)
    return required_permission in user_permissions

def get_permissions_for_roles(roles: List[str]) -> List[str]:
    """Get all permissions for a list of roles"""
    permissions = set()
    for role in roles:
        if role in ROLE_PERMISSIONS:
            permissions.update(ROLE_PERMISSIONS[role])
    return list(permissions)
```

### Claude Code RBAC Implementation Guidelines

1. **Use enums** for roles and permissions to ensure type safety
2. **Implement centralized permission mapping** rather than scattered checks
3. **Support multiple roles per user** for flexible authorization
4. **Provide helper functions** for common authorization patterns
5. **Validate roles and permissions** at the API boundary

## Rate Limiting Configurations

### In-Memory Rate Limiter Pattern

```python
class InMemoryRateLimiter:
    def __init__(self, max_attempts: int, window_seconds: int):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._hits: DefaultDict[str, List[float]] = defaultdict(list)

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

### Rate Limiter Integration

```python
class RateLimiterUtils:
    def __init__(self, config: Configuration):
        self.__login_rate_limiter = InMemoryRateLimiter(
            max_attempts=config.AUTH_RATE_LIMIT_ATTEMPTS,
            window_seconds=config.AUTH_RATE_LIMIT_WINDOW_SECONDS,
        )

    @property
    def login_rate_limiter(self) -> InMemoryRateLimiter:
        return self.__login_rate_limiter
```

### Usage in Endpoints

```python
# Apply rate limiting before authentication
if not rate_limiter.allow(client_ip):
    raise HTTPException(
        status_code=429,
        detail="Too many login attempts. Please try again later."
    )
```

### Production Rate Limiting Guidelines for Claude Code

1. **Use Redis-based rate limiting** in production environments
2. **Apply rate limiting by IP address** for brute force protection
3. **Implement sliding window algorithms** for more accurate limiting
4. **Configure different limits** for different endpoints (login vs. API calls)
5. **Include rate limit headers** in responses for client awareness

## Encryption Utility Usage

### GPG Encryption Pattern

```python
class EncryptionUtils:
    def __init__(self, config: Configuration):
        self.__config = config

    def encrypt_file(self, file_path: Path, *, recipient: str = None) -> Path:
        recipient_key = recipient or self.__config.GPG_RECIPIENT_KEY_ID
        if not recipient_key:
            raise EncryptionError("GPG_RECIPIENT_KEY_ID not configured")

        encrypted_path = file_path.with_suffix(file_path.suffix + ".gpg")
        cmd = [
            "gpg", "--batch", "--yes",
            "--recipient", recipient_key,
            "--output", str(encrypted_path),
            "--encrypt", str(file_path)
        ]

        subprocess.run(cmd, check=True, capture_output=True)
        return encrypted_path
```

### Encryption Integration Examples

```python
# Encrypt sensitive data before storage/transmission
encryption_utils = EncryptionUtils(config)
encrypted_backup = encryption_utils.encrypt_file(
    Path("/tmp/user_data.json"),
    recipient="admin@example.com"
)
```

### Claude Code Encryption Guidelines

1. **Use external GPG binary** to minimize dependency footprint
2. **Configure recipient keys** via environment variables
3. **Always verify file existence** before encryption
4. **Handle subprocess errors** gracefully with meaningful messages
5. **Return encrypted file paths** for further processing
6. **Never store encryption keys** in source code

## Security Best Practices Summary

### For JWT Implementation

- Implement automatic key rotation with distributed locking
- Use grace periods to prevent service disruption
- Include comprehensive audit logging
- Validate all JWT claims including required fields

### For RBAC Systems

- Use type-safe enums for roles and permissions
- Centralize permission mapping logic
- Support hierarchical permission inheritance
- Validate authorization at API boundaries

### For Rate Limiting

- Apply different limits for different endpoint types
- Use distributed rate limiting in production
- Include client feedback via response headers
- Implement progressive penalties for repeated violations

### For Data Encryption

- Use established encryption tools (GPG)
- Manage keys through secure configuration
- Encrypt sensitive data at rest and in transit
- Implement proper error handling for encryption failures
