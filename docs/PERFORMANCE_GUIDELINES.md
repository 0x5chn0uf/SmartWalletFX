# Performance Guidelines for Claude Code

This document outlines performance optimization patterns and best practices used in the trading bot codebase. These guidelines ensure efficient resource utilization, proper async/await usage, and optimized data access patterns.

## Async/Await Best Practices

### Context Manager Patterns

The codebase uses async context managers for resource management, particularly for Redis connections and distributed locking.

```python
from contextlib import asynccontextmanager
from typing import AsyncGenerator

@asynccontextmanager
async def acquire_lock(
    redis: Redis, lock_name: str, timeout: int
) -> AsyncGenerator[bool, None]:
    """Async context manager for distributed Redis locks"""
    lock_key = f"lock:{lock_name}"
    lock_acquired = await redis.set(lock_key, "locked", nx=True, ex=timeout)
    try:
        yield lock_acquired
    finally:
        if lock_acquired:
            await redis.delete(lock_key)

# Usage pattern
async def perform_critical_operation():
    async with acquire_lock(redis, "operation_lock", 300) as got_lock:
        if not got_lock:
            return  # Another process is handling this
        # Perform critical operation
```

### Async Repository Pattern

```python
class AsyncRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, entity_id: int) -> Optional[Entity]:
        result = await self.session.execute(
            select(Entity).where(Entity.id == entity_id)
        )
        return result.scalar_one_or_none()

    async def create_batch(self, entities: List[Entity]) -> List[Entity]:
        self.session.add_all(entities)
        await self.session.commit()
        return entities
```

### Async Service Layer Pattern

```python
class AsyncService:
    def __init__(self, repository: AsyncRepository, cache: Redis):
        self.repository = repository
        self.cache = cache

    async def get_with_cache(self, entity_id: int) -> Optional[Entity]:
        # Check cache first
        cache_key = f"entity:{entity_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            return Entity.model_validate_json(cached)

        # Fallback to database
        entity = await self.repository.get_by_id(entity_id)
        if entity:
            await self.cache.setex(
                cache_key,
                300,  # 5 minute TTL
                entity.model_dump_json()
            )
        return entity
```

### Claude Code Async Guidelines

1. **Always use async context managers** for resource cleanup
2. **Implement proper connection pooling** for database and Redis
3. **Use async/await consistently** throughout the call stack
4. **Handle connection failures gracefully** with fallback mechanisms
5. **Avoid blocking operations** in async contexts

## Redis Caching Strategies

### Cache-Aside Pattern

The primary caching pattern used throughout the application for read-heavy operations.

```python
async def get_jwks_cache(redis: Redis) -> Optional[JWKSet]:
    """Retrieve JWKS from Redis cache with graceful degradation"""
    try:
        cached_data = await redis.get(JWKS_CACHE_KEY)
        if cached_data:
            if isinstance(cached_data, bytes):
                cached_data = cached_data.decode("utf-8")
            jwks_dict = json.loads(cached_data)
            return JWKSet(**jwks_dict)
    except Exception as e:
        logger.warning("Failed to retrieve JWKS from cache: %s", e)
    return None

async def set_jwks_cache(redis: Redis, jwks: JWKSet, config: Configuration) -> bool:
    """Store JWKS in Redis cache with configured TTL"""
    try:
        serialized = json.dumps(jwks.model_dump())
        await redis.setex(JWKS_CACHE_KEY, config.JWKS_CACHE_TTL_SEC, serialized)
        return True
    except Exception as e:
        logger.warning("Failed to store JWKS in cache: %s", e)
        return False
```

### Write-Through Cache Invalidation

```python
async def invalidate_jwks_cache(redis: Redis) -> bool:
    """Explicitly invalidate cache after data changes"""
    try:
        deleted: int = await redis.delete(JWKS_CACHE_KEY)
        if deleted:
            logger.info("JWKS cache invalidated")
        return bool(deleted)
    except Exception as e:
        logger.warning("Failed to invalidate JWKS cache: %s", e)
        return False
```

### State Management Cache Pattern

```python
# OAuth state caching with TTL for security
async def store_state(redis: Redis, state: str, ttl: int = 300) -> bool:
    """Store OAuth state with automatic expiration"""
    try:
        await redis.setex(f"oauth:state:{state}", ttl, "1")
        return True
    except Exception:
        # Fallback to in-memory cache for development
        _memory_state_cache[state] = time.monotonic() + ttl
        return True

async def verify_state(redis: Redis, state: str) -> bool:
    """Verify and consume OAuth state (single use)"""
    try:
        key = f"oauth:state:{state}"
        exists = await redis.exists(key)
        if exists:
            await redis.delete(key)  # Consume the state
            return True
    except Exception:
        # Fallback verification
        expiry = _memory_state_cache.pop(state, None)
        return expiry is not None and expiry > time.monotonic()
    return False
```

### Claude Code Caching Guidelines

1. **Use consistent key naming conventions** (e.g., `entity:id`, `oauth:state:value`)
2. **Implement graceful degradation** when Redis is unavailable
3. **Set appropriate TTL values** based on data freshness requirements
4. **Invalidate caches immediately** after data modifications
5. **Use atomic operations** for state management (set with NX, delete after use)
6. **Handle serialization/deserialization** with proper error handling

## Database Query Optimization

### Efficient Query Patterns

```python
# Use select() with specific columns when possible
async def get_user_summary(session: AsyncSession, user_id: int):
    result = await session.execute(
        select(User.id, User.email, User.created_at)
        .where(User.id == user_id)
    )
    return result.first()

# Batch operations for multiple records
async def create_portfolio_snapshots(
    session: AsyncSession,
    snapshots: List[PortfolioSnapshot]
) -> List[PortfolioSnapshot]:
    session.add_all(snapshots)
    await session.commit()
    return snapshots

# Use joins to avoid N+1 queries
async def get_wallets_with_balances(session: AsyncSession, user_id: int):
    result = await session.execute(
        select(Wallet)
        .options(selectinload(Wallet.token_balances))
        .where(Wallet.user_id == user_id)
    )
    return result.scalars().all()
```

### Connection Management

```python
# Use dependency injection for session management
async def get_db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Repository pattern with proper session handling
class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
```

### Claude Code Database Guidelines

1. **Use async sessions consistently** throughout the application
2. **Implement proper error handling** for database operations
3. **Use eager loading** (selectinload) to avoid N+1 queries
4. **Batch operations** when working with multiple records
5. **Close sessions properly** using dependency injection or context managers
6. **Use specific column selection** when full objects aren't needed

## Background Task Patterns with Celery

### Task Definition with Error Handling

```python
@celery.task(bind=True, name="app.tasks.jwt_rotation.promote_and_retire_keys_task")
def promote_and_retire_keys_task(self):
    """Celery task with proper error handling and retry logic"""

    async def _run():
        redis = _build_redis_client()
        try:
            async with acquire_lock(
                redis, "jwt_key_rotation",
                timeout=_config.JWT_ROTATION_LOCK_TTL_SEC
            ) as got_lock:
                if not got_lock:
                    Audit.debug("Lock not acquired – skipping run.")
                    return

                # Perform the actual work
                key_set = _gather_current_key_set()
                update = promote_and_retire_keys(key_set, datetime.now(timezone.utc))

                if not update.is_noop():
                    _apply_key_set_update(update)
        finally:
            await redis.close()

    try:
        asyncio.run(_run())
    except Exception as exc:
        # Exponential backoff retry
        retry_delay = min(60 * 60, (self.request.retries + 1) * 60)
        raise self.retry(exc=exc, countdown=retry_delay)
```

### Celery Configuration Pattern

```python
class CoreCelery:
    def __init__(self, config: Configuration):
        self.config = config
        self._celery_app = Celery(
            config.PROJECT_NAME,
            broker=config.REDIS_URL,
            backend=config.REDIS_URL,
        )
        self._celery_app.conf.timezone = "UTC"
        self._setup_beat_schedule()

    def _setup_beat_schedule(self):
        """Configure periodic tasks"""
        self._celery_app.conf.beat_schedule = {
            "jwt-rotation-beat": {
                "task": "app.tasks.jwt_rotation.promote_and_retire_keys_task",
                "schedule": crontab(*self.config.JWT_ROTATION_SCHEDULE_CRON.split()),
            }
        }
```

### Metrics and Monitoring Integration

```python
# Prometheus metrics for task monitoring
try:
    from prometheus_client import Counter

    _TASK_SUCCESS_C = Counter(
        "celery_task_success_total",
        "Number of successful task executions",
        ["task_name"]
    )
    _TASK_ERROR_C = Counter(
        "celery_task_error_total",
        "Number of task execution errors",
        ["task_name"]
    )
except ImportError:
    # Graceful degradation if prometheus_client not available
    class _NoOpMetric:
        def inc(self, *args, **kwargs):
            pass

    _TASK_SUCCESS_C = _NoOpMetric()
    _TASK_ERROR_C = _NoOpMetric()
```

### Claude Code Celery Guidelines

1. **Use distributed locking** for tasks that shouldn't run concurrently
2. **Implement exponential backoff** for retry mechanisms
3. **Include comprehensive logging** for task execution tracking
4. **Use async patterns** within Celery tasks when appropriate
5. **Configure proper error handling** with meaningful error messages
6. **Include metrics collection** for monitoring task performance
7. **Set appropriate timeouts** and TTL values for distributed locks

## Performance Monitoring Patterns

### Redis Connection Pooling

```python
# Singleton pattern for Redis connections
_redis_singleton: Redis | None = None

def _build_redis_client() -> Redis:
    global _redis_singleton
    if _redis_singleton is None:
        config = Configuration()
        _redis_singleton = Redis.from_url(config.redis_url)
    return _redis_singleton
```

### Resource Cleanup Patterns

```python
# Always clean up resources in finally blocks
async def cache_operation():
    redis = _build_redis_client()
    try:
        await redis.set("key", "value")
    finally:
        await redis.close()

# Or use context managers for automatic cleanup
async with Redis.from_url(redis_url) as redis:
    await redis.set("key", "value")
    # Connection automatically closed
```

### Error Boundary Pattern

```python
async def resilient_cache_get(key: str) -> Optional[str]:
    """Cache retrieval with fallback on failure"""
    try:
        redis = _build_redis_client()
        value = await redis.get(key)
        return value.decode() if value else None
    except Exception as e:
        logger.warning("Cache retrieval failed for key %s: %s", key, e)
        return None  # Graceful degradation
```

## Performance Best Practices Summary

### For Async Operations

- Use async context managers for resource management
- Implement proper connection pooling and cleanup
- Handle exceptions gracefully with fallback mechanisms
- Avoid blocking calls in async contexts

### For Caching

- Implement cache-aside pattern with TTL
- Use consistent naming conventions for cache keys
- Provide graceful degradation when cache is unavailable
- Invalidate caches immediately after data changes

### For Database Access

- Use async sessions with proper dependency injection
- Implement eager loading to avoid N+1 queries
- Batch operations when working with multiple records
- Use specific column selection for better performance

### For Background Tasks

- Use distributed locking for critical tasks
- Implement exponential backoff for retries
- Include comprehensive monitoring and metrics
- Handle async operations properly within Celery tasks
