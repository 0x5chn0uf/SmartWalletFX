"""JWKS endpoint for serving JSON Web Key Sets."""

import importlib
import logging

from fastapi import APIRouter

from app.schemas.jwks import JWKSet
from app.utils.jwks_cache import (
    _build_redis_client,
    get_jwks_cache,
    set_jwks_cache,
)
from app.utils.jwt_keys import format_public_key_to_jwk, get_verifying_keys

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/.well-known/jwks.json", response_model=JWKSet)
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
            logger.debug("JWKS served from cache")
            # Emit audit event for cache hit
            try:
                audit_mod = importlib.import_module("app.utils.logging")
                audit_mod.audit(
                    "JWKS_REQUESTED", cache_hit=True, keys_count=len(cached_jwks.keys)
                )
            except Exception as audit_exc:  # pragma: no cover
                logger.debug("Audit logging failed: %s", audit_exc)
            return cached_jwks
    except Exception as e:
        logger.warning("Cache lookup failed, falling back to uncached: %s", e)
    finally:
        try:
            await redis.close()
        except Exception as e:
            logger.warning("Failed to close Redis connection: %s", e)

    # Cache miss or error - generate fresh JWKS
    verifying_keys = get_verifying_keys()

    # Format each key as a JWK
    jwks = []
    for key in verifying_keys:
        try:
            jwk = format_public_key_to_jwk(key.value, key.kid)
            jwks.append(jwk)
        except Exception as e:
            logger.warning("Failed to format key %s: %s", key.kid, e)
            continue

    jwks_response = JWKSet(keys=jwks)

    # Emit audit event for cache miss / fresh generation
    try:
        audit_mod = importlib.import_module("app.utils.logging")
        audit_mod.audit("JWKS_REQUESTED", cache_hit=False, keys_count=len(jwks))
    except Exception as audit_exc:  # pragma: no cover
        logger.debug("Audit logging failed: %s", audit_exc)

    # Cache the result (fire and forget - don't block response)
    redis = _build_redis_client()
    try:
        await set_jwks_cache(redis, jwks_response)
        logger.debug("JWKS cached successfully")
    except Exception as e:
        logger.warning("Failed to cache JWKS: %s", e)
    finally:
        try:
            await redis.close()
        except Exception as e:
            logger.warning("Failed to close Redis connection: %s", e)

    return jwks_response
