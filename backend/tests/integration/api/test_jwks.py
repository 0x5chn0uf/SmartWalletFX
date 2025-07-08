"""Integration tests for the JWKS endpoint."""
import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from tests.fixtures.deduplicated import sample_jwks


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


@pytest.mark.asyncio
async def test_jwks_endpoint_empty_key_set(test_app):
    """JWKS endpoint should return empty key set when no keys are available."""
    # Mock get_verifying_keys to return empty list
    with patch("app.api.endpoints.jwks.get_verifying_keys", return_value=[]):
        # Mock cache to return None (miss)
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        mock_redis.close.return_value = None

        with patch(
            "app.api.endpoints.jwks._build_redis_client", return_value=mock_redis
        ):
            transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=True)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://test"
            ) as ac:
                resp = await ac.get("/.well-known/jwks.json")

    assert resp.status_code == 200
    data = resp.json()
    assert "keys" in data
    assert data["keys"] == []  # Empty key set


@pytest.mark.asyncio
async def test_jwks_endpoint_key_formatting_failure_graceful(test_app):
    """JWKS endpoint should handle key formatting failures gracefully."""
    from app.utils.jwt_rotation import Key

    # Create a mock key that will cause formatting to fail
    mock_key = Key(kid="bad-key", value="invalid-key-data", retired_at=None)

    # Mock get_verifying_keys to return a key that will fail formatting
    with patch("app.api.endpoints.jwks.get_verifying_keys", return_value=[mock_key]):
        # Mock format_public_key_to_jwk to raise an exception
        with patch(
            "app.api.endpoints.jwks.format_public_key_to_jwk",
            side_effect=Exception("Key formatting failed"),
        ):
            # Mock cache to return None (miss)
            mock_redis = AsyncMock()
            mock_redis.get.return_value = None
            mock_redis.setex.return_value = True
            mock_redis.close.return_value = None

            with patch(
                "app.api.endpoints.jwks._build_redis_client", return_value=mock_redis
            ):
                transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=True)
                async with httpx.AsyncClient(
                    transport=transport, base_url="http://test"
                ) as ac:
                    resp = await ac.get("/.well-known/jwks.json")

    assert resp.status_code == 200
    data = resp.json()
    assert "keys" in data
    assert data["keys"] == []  # Should return empty key set when formatting fails


@pytest.mark.asyncio
async def test_jwks_endpoint_mixed_key_formatting_success_and_failure(test_app):
    """JWKS endpoint should include successfully formatted keys even when some fail."""
    from app.utils.jwt_rotation import Key

    # Create two keys: one that will succeed, one that will fail
    good_key = Key(kid="good-key", value="valid-key-data", retired_at=None)
    bad_key = Key(kid="bad-key", value="invalid-key-data", retired_at=None)

    # Mock get_verifying_keys to return both keys
    with patch(
        "app.api.endpoints.jwks.get_verifying_keys", return_value=[good_key, bad_key]
    ):
        # Mock format_public_key_to_jwk to succeed for good key, fail for bad key
        def mock_format_key(key_value, kid):
            if kid == "good-key":
                return {
                    "kty": "RSA",
                    "use": "sig",
                    "kid": "good-key",
                    "alg": "RS256",
                    "n": "test-modulus",
                    "e": "AQAB",
                }
            else:
                raise Exception("Key formatting failed")

        with patch(
            "app.api.endpoints.jwks.format_public_key_to_jwk",
            side_effect=mock_format_key,
        ):
            # Mock cache to return None (miss)
            mock_redis = AsyncMock()
            mock_redis.get.return_value = None
            mock_redis.setex.return_value = True
            mock_redis.close.return_value = None

            with patch(
                "app.api.endpoints.jwks._build_redis_client", return_value=mock_redis
            ):
                transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=True)
                async with httpx.AsyncClient(
                    transport=transport, base_url="http://test"
                ) as ac:
                    resp = await ac.get("/.well-known/jwks.json")

    assert resp.status_code == 200
    data = resp.json()
    assert "keys" in data
    assert len(data["keys"]) == 1  # Should include only the successfully formatted key
    assert data["keys"][0]["kid"] == "good-key"


@pytest.mark.asyncio
async def test_jwks_endpoint_cache_close_failure_graceful(test_app):
    """JWKS endpoint should handle Redis close failures gracefully."""
    # Mock Redis to fail on close
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.setex.return_value = True
    mock_redis.close.side_effect = Exception("Redis close failed")

    with patch("app.api.endpoints.jwks._build_redis_client", return_value=mock_redis):
        transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=True)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/.well-known/jwks.json")

    assert resp.status_code == 200
    data = resp.json()
    assert "keys" in data
    # Should still return a valid response despite Redis close failure


@pytest.mark.asyncio
async def test_jwks_endpoint_concurrent_requests(test_app):
    """JWKS endpoint should handle concurrent requests correctly."""
    import asyncio

    # Mock cache to return None (miss) for all requests
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.setex.return_value = True
    mock_redis.close.return_value = None

    with patch("app.api.endpoints.jwks._build_redis_client", return_value=mock_redis):
        transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=True)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            # Make multiple concurrent requests
            tasks = [ac.get("/.well-known/jwks.json") for _ in range(5)]
            responses = await asyncio.gather(*tasks)

    # All requests should succeed
    for resp in responses:
        assert resp.status_code == 200
        data = resp.json()
        assert "keys" in data
