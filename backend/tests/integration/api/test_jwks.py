"""Integration tests for the JWKS endpoint."""

import httpx
import pytest


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
