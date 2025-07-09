import pytest

from app.schemas.jwks import JWK, JWKSet


@pytest.fixture
def sample_jwks():
    """Create a sample JWKSet for testing."""
    jwk = JWK(
        kty="RSA",
        use="sig",
        kid="test-key-1",
        alg="RS256",
        n="test-modulus",
        e="AQAB",
    )
    return JWKSet(keys=[jwk])
