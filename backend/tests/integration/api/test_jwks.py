"""Integration tests for the JWKS endpoint."""

import json
from unittest.mock import AsyncMock, patch

import httpx
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


@pytest.mark.asyncio
async def test_jwks_endpoint_returns_jwks_format(test_app):
    """JWKS endpoint should return a valid JWKSet format."""
    transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=True)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/.well-known/jwks.json")

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"

    data = resp.json()
    assert "keys" in data
    assert isinstance(data["keys"], list)


@pytest.mark.asyncio
async def test_jwks_endpoint_structure(test_app):
    """JWKS endpoint should return properly structured JWK objects."""
    transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=True)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/.well-known/jwks.json")

    assert resp.status_code == 200
    data = resp.json()

    # If there are keys, they should have the required JWK fields
    if data["keys"]:
        key = data["keys"][0]
        required_fields = ["kty", "use", "kid", "alg", "n", "e"]
        for field in required_fields:
            assert field in key, f"JWK missing required field: {field}"

        # Validate specific values for RSA keys
        assert key["kty"] == "RSA"
        assert key["use"] == "sig"
        assert key["alg"] == "RS256"


@pytest.mark.asyncio
async def test_jwks_endpoint_cache_hit(test_app, sample_jwks):
    """JWKS endpoint should serve cached response when available."""
    # Mock the cache to return a cached response
    mock_redis = AsyncMock()
    mock_redis.get.return_value = json.dumps(sample_jwks.model_dump()).encode()
    mock_redis.close.return_value = None

    with patch("app.api.endpoints.jwks._build_redis_client", return_value=mock_redis):
        transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=True)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/.well-known/jwks.json")

    assert resp.status_code == 200
    data = resp.json()
    assert data["keys"] == sample_jwks.model_dump()["keys"]


@pytest.mark.asyncio
async def test_jwks_endpoint_cache_miss(test_app):
    """JWKS endpoint should generate fresh response on cache miss."""
    # Mock the cache to return None (cache miss)
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.setex.return_value = True
    mock_redis.close.return_value = None

    with patch("app.api.endpoints.jwks._build_redis_client", return_value=mock_redis):
        transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=True)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/.well-known/jwks.json")

    assert resp.status_code == 200
    data = resp.json()
    assert "keys" in data
    # Should have called setex to cache the result
    mock_redis.setex.assert_called()


@pytest.mark.asyncio
async def test_jwks_endpoint_redis_error_graceful_fallback(test_app):
    """JWKS endpoint should work when Redis is unavailable."""
    # Mock Redis to raise an exception
    mock_redis = AsyncMock()
    mock_redis.get.side_effect = Exception("Redis connection failed")
    mock_redis.close.return_value = None

    with patch("app.api.endpoints.jwks._build_redis_client", return_value=mock_redis):
        transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=True)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/.well-known/jwks.json")

    assert resp.status_code == 200
    data = resp.json()
    assert "keys" in data
    # Should still return a valid response despite Redis error


@pytest.mark.asyncio
async def test_jwks_endpoint_cache_storage_error_graceful(test_app):
    """JWKS endpoint should work when cache storage fails."""
    # Mock cache get to return None (miss) and setex to fail
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.setex.side_effect = Exception("Redis storage failed")
    mock_redis.close.return_value = None

    with patch("app.api.endpoints.jwks._build_redis_client", return_value=mock_redis):
        transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=True)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/.well-known/jwks.json")

    assert resp.status_code == 200
    data = resp.json()
    assert "keys" in data
    # Should still return a valid response despite cache storage failure
