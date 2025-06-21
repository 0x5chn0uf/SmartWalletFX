"""JWKS endpoint for serving JSON Web Key Sets."""

from fastapi import APIRouter

from app.schemas.jwks import JWKSet
from app.utils.jwt_keys import format_public_key_to_jwk, get_verifying_keys

router = APIRouter()


@router.get("/.well-known/jwks.json", response_model=JWKSet)
async def get_jwks():
    """Return the JSON Web Key Set for JWT verification.

    This endpoint provides the public keys needed by clients to verify
    JWT signatures. The keys are returned in the standard JWK format
    as defined by RFC 7517.

    Returns:
        JWKSet: A JSON Web Key Set containing all active public keys.
    """
    # Get all currently valid keys for verification
    verifying_keys = get_verifying_keys()

    # Format each key as a JWK
    jwks = []
    for key in verifying_keys:
        try:
            jwk = format_public_key_to_jwk(key.value, key.kid)
            jwks.append(jwk)
        except Exception:
            # Log the error but continue processing other keys
            # This prevents a single malformed key from breaking the entire endpoint
            continue

    # Return the JWKSet
    return JWKSet(keys=jwks)
