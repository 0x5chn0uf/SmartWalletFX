"""Redis caching utilities for JWKS endpoint."""

import asyncio
import json
import logging
from typing import Optional

from redis.asyncio import Redis

from app.core.config import Configuration
from app.domain.interfaces.utils import JWKSCacheUtilsInterface
from app.domain.schemas.jwks import JWKSet

logger = logging.getLogger(__name__)

# Cache key for JWKS - static since content is the same for all clients
JWKS_CACHE_KEY = "jwks:current"


class JWKSCacheUtils(JWKSCacheUtilsInterface):
    """Utility class for JWKS caching operations."""

    def __init__(self, config: Configuration):
        """Initialize JWKSCacheUtils with dependencies."""
        self.__config = config
        self._redis_client: Redis | None = None

    def _build_redis_client(self) -> Redis:
        """Return an *async* Redis client using ``Configuration.redis_url``."""
        if self._redis_client is None:
            redis_url = self.__config.redis_url
            self._redis_client = Redis.from_url(redis_url)
        return self._redis_client

    async def get_jwks_cache(self, redis: Redis) -> Optional[JWKSet]:
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

    async def set_jwks_cache(self, redis: Redis, jwks: JWKSet) -> bool:
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
            await redis.setex(
                JWKS_CACHE_KEY, self.__config.JWKS_CACHE_TTL_SEC, serialized
            )
            return True
        except Exception as e:
            logger.warning("Failed to store JWKS in cache: %s", e)
            return False

    async def invalidate_jwks_cache(self, redis: Redis) -> bool:
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

    def invalidate_jwks_cache_sync(self) -> bool:
        """Synchronous wrapper for JWKS cache invalidation."""
        try:
            redis = self._build_redis_client()
            result = asyncio.run(self.invalidate_jwks_cache(redis))
            asyncio.run(redis.close())
            return result
        except Exception as e:
            logger.warning("Failed to invalidate JWKS cache (sync): %s", e)
            return False
