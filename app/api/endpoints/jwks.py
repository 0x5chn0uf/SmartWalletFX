"""JWKS endpoint for serving JSON Web Key Sets."""

from fastapi import APIRouter

from app.domain.schemas.jwks import JWKSet
from app.usecase.jwks_usecase import JWKSUsecase


class JWKS:
    """JWKS endpoint using singleton pattern with dependency injection."""

    ep = APIRouter(tags=["jwks"])
    __jwks_uc: JWKSUsecase

    def __init__(self, jwks_usecase: JWKSUsecase):
        """Initialize with injected dependencies."""
        JWKS.__jwks_uc = jwks_usecase

    @staticmethod
    @ep.get("/.well-known/jwks.json", response_model=JWKSet)
    async def get_jwks() -> JWKSet:
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
        return await JWKS.__jwks_uc.get_jwks()
