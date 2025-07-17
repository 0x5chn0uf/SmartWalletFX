"""JWKS endpoint for serving JSON Web Key Sets."""

from fastapi import APIRouter

from app.domain.schemas.jwks import JWKSet
from app.utils.jwks_cache import (
    _build_redis_client,
    get_jwks_cache,
    set_jwks_cache,
)
from app.utils.jwt_keys import format_public_key_to_jwk, get_verifying_keys
from app.utils.logging import Audit


class JWKS:
    """JWKS endpoint using singleton pattern with dependency injection."""

    ep = APIRouter(tags=["jwks"])

    def __init__(self):
        """Initialize JWKS endpoint."""
        pass

    @staticmethod
    @ep.get("/.well-known/jwks.json", response_model=JWKSet)
    async def get_jwks():
        """Return the JSON Web Key Set for JWT verification.

        This endpoint provides the public keys needed by clients to verify
        JWT signatures. The keys are returned in the standard JWK format
        as defined by RFC 7517.

        The response is cached in Redis to improve performance. The cache
        is invalidated when keys are rotated to ensure fresh keys are
        published immediately.

        Returns:
            JWKSet: A JSON Web Key Set containing all active public keys.
        """
        # Try to get from cache first
        redis = _build_redis_client()
        try:
            cached_jwks = await get_jwks_cache(redis)
            if cached_jwks:
                Audit.debug("JWKS served from cache")
                # Emit audit event for cache hit
                try:
                    Audit.info(
                        "JWKS requested",
                        cache_hit=True,
                        keys_count=len(cached_jwks.keys),
                    )
                except Exception as audit_exc:  # pragma: no cover
                    Audit.debug(f"Audit logging failed: {audit_exc}")
                return cached_jwks
        except Exception as e:
            Audit.warning(f"Cache lookup failed, falling back to uncached: {e}")
        finally:
            try:
                await redis.close()
            except Exception as e:
                Audit.warning(f"Failed to close Redis connection: {e}")

        # Cache miss or error - generate fresh JWKS
        verifying_keys = get_verifying_keys()

        # Format each key as a JWK
        jwks = []
        for key in verifying_keys:
            try:
                jwk = format_public_key_to_jwk(key.value, key.kid)
                jwks.append(jwk)
            except Exception as e:
                Audit.warning(f"Failed to format key {key.kid}: {e}")
                continue

        jwks_response = JWKSet(keys=jwks)

        # Emit audit event for cache miss / fresh generation
        try:
            Audit.info("JWKS requested", cache_hit=False, keys_count=len(jwks))
        except Exception as audit_exc:  # pragma: no cover
            Audit.debug(f"Audit logging failed: {audit_exc}")

        # Cache the result (fire and forget - don't block response)
        redis = _build_redis_client()
        try:
            await set_jwks_cache(redis, jwks_response)
            Audit.debug("JWKS cached successfully")
        except Exception as e:
            Audit.warning(f"Failed to cache JWKS: {e}")
        finally:
            try:
                await redis.close()
            except Exception as e:
                Audit.warning(f"Failed to close Redis connection: {e}")

        return jwks_response
