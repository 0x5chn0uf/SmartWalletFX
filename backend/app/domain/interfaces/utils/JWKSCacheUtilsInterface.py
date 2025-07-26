from __future__ import annotations

from abc import ABC, abstractmethod

from redis.asyncio import Redis

from app.domain.schemas.jwks import JWKSet


class JWKSCacheUtilsInterface(ABC):
    """Interface for JWKS caching helpers."""

    @abstractmethod
    async def set_jwks_cache(self, redis: Redis, jwks: JWKSet) -> bool:
        """Store JWKS in Redis cache."""

    @abstractmethod
    def invalidate_jwks_cache_sync(self) -> bool:
        """Invalidate JWKS cache synchronously."""
