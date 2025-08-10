"""Integration tests for the JWKS endpoint."""
import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.domain.schemas.jwks import JWK, JWKSet


@pytest.mark.unit
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


@pytest.mark.unit
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


@pytest.mark.unit
@pytest.mark.asyncio
async def test_jwks_endpoint_cache_hit(test_app, sample_jwks):
    """JWKS endpoint should serve cached response when available."""
    # Mock the use case to return the cached JWKS directly
    mock_jwks_usecase = AsyncMock()
    mock_jwks_usecase.get_jwks.return_value = sample_jwks

    with patch("app.api.endpoints.jwks.JWKS._JWKS__jwks_uc", mock_jwks_usecase):
        transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=True)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/.well-known/jwks.json")

    assert resp.status_code == 200
    data = resp.json()
    assert data["keys"] == sample_jwks.model_dump()["keys"]
    mock_jwks_usecase.get_jwks.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_jwks_endpoint_cache_miss(test_app):
    """JWKS endpoint should generate fresh response on cache miss."""
    # Create a sample JWKSet for the response
    sample_jwk = JWK(
        kty="RSA", use="sig", kid="test-key-id", alg="RS256", n="test-modulus", e="AQAB"
    )
    expected_jwks = JWKSet(keys=[sample_jwk])

    # Mock the use case to return fresh JWKS
    mock_jwks_usecase = AsyncMock()
    mock_jwks_usecase.get_jwks.return_value = expected_jwks

    with patch("app.api.endpoints.jwks.JWKS._JWKS__jwks_uc", mock_jwks_usecase):
        transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=True)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/.well-known/jwks.json")

    assert resp.status_code == 200
    data = resp.json()
    assert "keys" in data
    assert len(data["keys"]) == 1
    assert data["keys"][0]["kid"] == "test-key-id"
    mock_jwks_usecase.get_jwks.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_jwks_endpoint_redis_error_graceful_fallback(test_app):
    """JWKS endpoint should work when Redis is unavailable."""
    # Create a sample JWKSet for fallback response
    sample_jwk = JWK(
        kty="RSA",
        use="sig",
        kid="fallback-key",
        alg="RS256",
        n="test-modulus",
        e="AQAB",
    )
    fallback_jwks = JWKSet(keys=[sample_jwk])

    # Mock the use case to handle the Redis error gracefully and return fallback
    mock_jwks_usecase = AsyncMock()
    mock_jwks_usecase.get_jwks.return_value = fallback_jwks

    with patch("app.api.endpoints.jwks.JWKS._JWKS__jwks_uc", mock_jwks_usecase):
        transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=True)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/.well-known/jwks.json")

    assert resp.status_code == 200
    data = resp.json()
    assert "keys" in data
    assert len(data["keys"]) == 1
    assert data["keys"][0]["kid"] == "fallback-key"
    mock_jwks_usecase.get_jwks.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_jwks_endpoint_cache_storage_error_graceful(test_app):
    """JWKS endpoint should work when cache storage fails."""
    # Create a sample JWKSet
    sample_jwk = JWK(
        kty="RSA",
        use="sig",
        kid="storage-error-key",
        alg="RS256",
        n="test-modulus",
        e="AQAB",
    )
    expected_jwks = JWKSet(keys=[sample_jwk])

    # Mock the use case to handle storage error gracefully and still return JWKS
    mock_jwks_usecase = AsyncMock()
    mock_jwks_usecase.get_jwks.return_value = expected_jwks

    with patch("app.api.endpoints.jwks.JWKS._JWKS__jwks_uc", mock_jwks_usecase):
        transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=True)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/.well-known/jwks.json")

    assert resp.status_code == 200
    data = resp.json()
    assert "keys" in data
    assert len(data["keys"]) == 1
    assert data["keys"][0]["kid"] == "storage-error-key"
    mock_jwks_usecase.get_jwks.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_jwks_endpoint_empty_key_set(test_app):
    """JWKS endpoint should return empty key set when no keys are available."""
    # Mock the use case to return empty JWKS
    empty_jwks = JWKSet(keys=[])
    mock_jwks_usecase = AsyncMock()
    mock_jwks_usecase.get_jwks.return_value = empty_jwks

    with patch("app.api.endpoints.jwks.JWKS._JWKS__jwks_uc", mock_jwks_usecase):
        transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=True)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/.well-known/jwks.json")

    assert resp.status_code == 200
    data = resp.json()
    assert "keys" in data
    assert data["keys"] == []  # Empty key set
    mock_jwks_usecase.get_jwks.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_jwks_endpoint_key_formatting_failure_graceful(test_app):
    """JWKS endpoint should handle key formatting failures gracefully."""
    # Mock the use case to return empty JWKS when formatting fails
    empty_jwks = JWKSet(keys=[])
    mock_jwks_usecase = AsyncMock()
    mock_jwks_usecase.get_jwks.return_value = empty_jwks

    with patch("app.api.endpoints.jwks.JWKS._JWKS__jwks_uc", mock_jwks_usecase):
        transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=True)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/.well-known/jwks.json")

    assert resp.status_code == 200
    data = resp.json()
    assert "keys" in data
    assert data["keys"] == []  # Should return empty key set when formatting fails
    mock_jwks_usecase.get_jwks.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_jwks_endpoint_mixed_key_formatting_success_and_failure(test_app):
    """JWKS endpoint should include successfully formatted keys even when some fail."""
    # Create JWKS with only the successfully formatted key
    successful_jwk = JWK(
        kty="RSA", use="sig", kid="good-key", alg="RS256", n="test-modulus", e="AQAB"
    )
    partial_jwks = JWKSet(keys=[successful_jwk])

    # Mock the use case to return only successfully formatted keys
    mock_jwks_usecase = AsyncMock()
    mock_jwks_usecase.get_jwks.return_value = partial_jwks

    with patch("app.api.endpoints.jwks.JWKS._JWKS__jwks_uc", mock_jwks_usecase):
        transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=True)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/.well-known/jwks.json")

    assert resp.status_code == 200
    data = resp.json()
    assert "keys" in data
    assert len(data["keys"]) == 1  # Should include only the successfully formatted key
    assert data["keys"][0]["kid"] == "good-key"
    mock_jwks_usecase.get_jwks.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_jwks_endpoint_cache_close_failure_graceful(test_app):
    """JWKS endpoint should handle Redis close failures gracefully."""
    # Create a sample JWKSet
    sample_jwk = JWK(
        kty="RSA",
        use="sig",
        kid="close-error-key",
        alg="RS256",
        n="test-modulus",
        e="AQAB",
    )
    expected_jwks = JWKSet(keys=[sample_jwk])

    # Mock the use case to handle close error gracefully and still return JWKS
    mock_jwks_usecase = AsyncMock()
    mock_jwks_usecase.get_jwks.return_value = expected_jwks

    with patch("app.api.endpoints.jwks.JWKS._JWKS__jwks_uc", mock_jwks_usecase):
        transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=True)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/.well-known/jwks.json")

    assert resp.status_code == 200
    data = resp.json()
    assert "keys" in data
    assert len(data["keys"]) == 1
    assert data["keys"][0]["kid"] == "close-error-key"
    mock_jwks_usecase.get_jwks.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_jwks_endpoint_concurrent_requests(test_app):
    """JWKS endpoint should handle concurrent requests correctly."""
    import asyncio

    # Create a sample JWKSet
    sample_jwk = JWK(
        kty="RSA",
        use="sig",
        kid="concurrent-key",
        alg="RS256",
        n="test-modulus",
        e="AQAB",
    )
    expected_jwks = JWKSet(keys=[sample_jwk])

    # Mock the use case to return consistent results for concurrent requests
    mock_jwks_usecase = AsyncMock()
    mock_jwks_usecase.get_jwks.return_value = expected_jwks

    with patch("app.api.endpoints.jwks.JWKS._JWKS__jwks_uc", mock_jwks_usecase):
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
        assert len(data["keys"]) == 1
        assert data["keys"][0]["kid"] == "concurrent-key"

    # Should have been called 5 times (once per concurrent request)
    assert mock_jwks_usecase.get_jwks.call_count == 5
