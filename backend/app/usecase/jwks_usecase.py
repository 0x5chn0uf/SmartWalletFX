"""JWKS use case for managing JSON Web Key Set operations."""

from typing import Optional

from app.domain.schemas.jwks import JWKSet
from app.utils.jwks_cache import JWKSCacheUtils
from app.utils.jwt_keys import JWTKeyUtils
from app.utils.logging import Audit


class JWKSUsecase:
    """Use case for JWKS operations following DDD principles."""

    def __init__(
        self, jwks_cache_utils: JWKSCacheUtils, jwt_key_utils: JWTKeyUtils, audit: Audit
    ):
        """Initialize with dependencies."""
        self.jwks_cache_utils = jwks_cache_utils
        self.jwt_key_utils = jwt_key_utils
        self.audit = audit

    async def get_jwks(self) -> JWKSet:
        """Get JWKS with caching logic.

        Returns:
            JWKSet: The current JSON Web Key Set
        """
        # Try to get from cache first
        cached_jwks = await self._get_cached_jwks()
        if cached_jwks:
            self.audit.debug("JWKS served from cache")
            self.audit.info(
                "JWKS requested", cache_hit=True, keys_count=len(cached_jwks.keys)
            )
            return cached_jwks

        # Cache miss - generate fresh JWKS
        jwks_response = await self._generate_fresh_jwks()
        self.audit.info(
            "JWKS requested", cache_hit=False, keys_count=len(jwks_response.keys)
        )

        # Cache the result (fire and forget - don't block response)
        await self._cache_jwks(jwks_response)

        return jwks_response

    async def _get_cached_jwks(self) -> Optional[JWKSet]:
        """Attempt to retrieve JWKS from cache."""
        redis = self.jwks_cache_utils._build_redis_client()
        try:
            return await self.jwks_cache_utils.get_jwks_cache(redis)
        except Exception as e:
            self.audit.warning(f"Cache lookup failed, falling back to uncached: {e}")
            return None
        finally:
            try:
                await redis.close()
            except Exception as e:
                self.audit.warning(f"Failed to close Redis connection: {e}")

    async def _generate_fresh_jwks(self) -> JWKSet:
        """Generate a fresh JWKS from current keys."""
        verifying_keys = self.jwt_key_utils.get_verifying_keys()

        # Format each key as a JWK
        jwks = []
        for key in verifying_keys:
            try:
                jwk = self.jwt_key_utils.format_public_key_to_jwk(key.value, key.kid)
                jwks.append(jwk)
            except Exception as e:
                self.audit.warning(f"Failed to format key {key.kid}: {e}")
                continue

        return JWKSet(keys=jwks)

    async def _cache_jwks(self, jwks: JWKSet) -> None:
        """Cache the JWKS response."""
        redis = self.jwks_cache_utils._build_redis_client()
        try:
            await self.jwks_cache_utils.set_jwks_cache(redis, jwks)
            self.audit.debug("JWKS cached successfully")
        except Exception as e:
            self.audit.warning(f"Failed to cache JWKS: {e}")
        finally:
            try:
                await redis.close()
            except Exception as e:
                self.audit.warning(f"Failed to close Redis connection: {e}")
