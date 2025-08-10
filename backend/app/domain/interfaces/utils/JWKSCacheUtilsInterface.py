from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from redis.asyncio import Redis

from app.domain.schemas.jwks import JWKSet


class JWKSCacheUtilsInterface(ABC):
    """Interface for JWKS caching helpers."""

    @abstractmethod
    def _build_redis_client(self) -> Redis:
        """Return an async Redis client using Configuration.redis_url."""

    @abstractmethod
    async def get_jwks_cache(self, redis: Redis) -> Optional[JWKSet]:
        """Retrieve JWKS from Redis cache."""

    @abstractmethod
    async def set_jwks_cache(self, redis: Redis, jwks: JWKSet) -> bool:
        """Store JWKS in Redis cache."""

    @abstractmethod
    async def invalidate_jwks_cache(self, redis: Redis) -> bool:
        """Explicitly invalidate the JWKS cache."""

    @abstractmethod
    def invalidate_jwks_cache_sync(self) -> bool:
        """Synchronous wrapper for JWKS cache invalidation."""
