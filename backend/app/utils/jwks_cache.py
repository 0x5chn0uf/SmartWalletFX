"""Redis caching utilities for JWKS endpoint."""

import asyncio
import json
import logging
from typing import Optional

from redis.asyncio import Redis

from app.core.config import settings
from app.schemas.jwks import JWKSet

logger = logging.getLogger(__name__)

# Cache key for JWKS - static since content is the same for all clients
JWKS_CACHE_KEY = "jwks:current"


async def get_jwks_cache(redis: Redis) -> Optional[JWKSet]:
    """Retrieve JWKS from Redis cache.

    Returns:
        JWKSet if found in cache, None if not found or error
    """
    try:
        cached_data = await redis.get(JWKS_CACHE_KEY)
        if cached_data:
            # Redis returns bytes, decode to string
            if isinstance(cached_data, bytes):
                cached_data = cached_data.decode("utf-8")
            jwks_dict = json.loads(cached_data)
            jwks_obj = JWKSet(**jwks_dict)
            return jwks_obj
    except Exception as e:
        logger.warning("Failed to retrieve JWKS from cache: %s", e)
    return None


async def set_jwks_cache(redis: Redis, jwks: JWKSet) -> bool:
    """Store JWKS in Redis cache with configured TTL.

    Returns:
        True if successfully cached, False on error
    """
    try:
        serialized = json.dumps(jwks.model_dump())
        # Note: Some internal libraries expect the order (key, value, ttl). We
        # follow that ordering here to ensure our property-based tests—which
        # patch the mock Redis client and introspect positional args—can make
        # the correct assertion about the TTL value being the *third* positional
        # argument (index 2).
        await redis.setex(JWKS_CACHE_KEY, settings.JWKS_CACHE_TTL_SEC, serialized)
        return True
    except Exception as e:
        logger.warning("Failed to store JWKS in cache: %s", e)
        return False


async def invalidate_jwks_cache(redis: Redis) -> bool:
    """Explicitly invalidate the JWKS cache.

    This function is called by the JWT rotation task to ensure
    fresh keys are published immediately after rotation.

    Returns:
        True if cache entry existed and was deleted, False otherwise or on error
    """
    try:
        deleted: int = await redis.delete(JWKS_CACHE_KEY)
        if deleted:
            logger.info("JWKS cache invalidated")
        else:
            logger.info("JWKS cache key not present; nothing to invalidate")
        return bool(deleted)
    except Exception as e:
        logger.warning("Failed to invalidate JWKS cache: %s", e)
        return False


def invalidate_jwks_cache_sync() -> bool:
    """Synchronous wrapper for JWKS cache invalidation.

    This function can be called from synchronous contexts like Celery tasks.
    It creates its own Redis client and handles the async/sync bridge.

    Returns:
        True if successfully invalidated, False on error
    """
    try:
        redis = _build_redis_client()
        # Use asyncio.run() to bridge async/sync
        result = asyncio.run(invalidate_jwks_cache(redis))
        asyncio.run(redis.close())
        return result
    except Exception as e:
        logger.warning("Failed to invalidate JWKS cache (sync): %s", e)
        return False


_redis_singleton: Redis | None = None


def _build_redis_client() -> Redis:
    """Return an *async* Redis client using ``settings.REDIS_URL`` if defined."""

    from app.core.config import settings  # local import to avoid cycles

    global _redis_singleton  # noqa: PLW0603 – module-level singleton

    if _redis_singleton is None:
        redis_url = settings.REDIS_URL or "redis://localhost:6379/0"
        _redis_singleton = Redis.from_url(redis_url)
    return _redis_singleton
