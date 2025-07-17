"""Property-based tests for JWKS endpoint using Hypothesis."""

import json
from typing import List, Optional
from unittest.mock import AsyncMock, patch

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from hypothesis.strategies import composite

from app.domain.schemas.jwks import JWK, JWKSet
from app.utils.jwt_rotation import Key


@composite
def key_sets(draw):
    """Generate various key sets for testing with unique ASCII alphanumeric kid values."""
    import string

    ascii_alphanum = string.ascii_letters + string.digits
    num_keys = draw(st.integers(min_value=0, max_value=3))  # Reduced from 5 to 3
    kids = draw(
        st.lists(
            st.text(min_size=1, max_size=20, alphabet=ascii_alphanum),
            min_size=num_keys,
            max_size=num_keys,
            unique=True,
        )
    )
    keys = []
    for kid in kids:
        is_valid = draw(st.booleans())
        if is_valid:
            # Generate a real RSA public key PEM with smaller key size for faster generation
            private_key = rsa.generate_private_key(
                public_exponent=65537, key_size=1024
            )  # Reduced from 2048 to 1024
            public_key = private_key.public_key()
            pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode()
            key = Key(kid=kid, value=pem)
        else:
            key = Key(kid=kid, value="invalid-key-data")
        keys.append(key)
    return keys


@composite
def cache_states(draw):
    """Generate various cache states for testing."""
    cache_hit = draw(st.booleans())
    cache_data = None

    if cache_hit:
        # Generate valid or invalid cached data
        is_valid_cache = draw(st.booleans())
        if is_valid_cache:
            jwk = JWK(
                kty="RSA",
                use="sig",
                kid="cached-key",
                alg="RS256",
                n="cached-modulus",
                e="AQAB",
            )
            cache_data = json.dumps(JWKSet(keys=[jwk]).model_dump())
        else:
            cache_data = "invalid-json-data"

    return cache_data


@pytest.mark.asyncio
@settings(
    max_examples=10,
    deadline=5000,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(key_set=key_sets(), cache_state=cache_states())
async def test_jwks_endpoint_property_based(
    key_set: List[Key], cache_state: Optional[str]
):
    """Property-based test for JWKS endpoint with various key sets and cache states."""

    # Patch get_verifying_keys before app creation
    def debug_get_verifying_keys():
        print(f"DEBUG: get_verifying_keys called, returning: {key_set}")
        return key_set

    with patch(
        "app.api.endpoints.jwks.get_verifying_keys",
        side_effect=debug_get_verifying_keys,
    ):
        from app.main import create_app

        test_app = create_app()

        # Mock Redis behavior based on cache state
        mock_redis = AsyncMock()
        if cache_state is not None:
            mock_redis.get.return_value = cache_state.encode() if cache_state else None
        else:
            mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        mock_redis.close.return_value = None

        with patch(
            "app.api.endpoints.jwks._build_redis_client", return_value=mock_redis
        ):
            # Mock key formatting to handle invalid keys gracefully
            def mock_format_key(key_value, kid):
                print(
                    f"DEBUG: format_public_key_to_jwk called for kid={kid}, value={key_value[:30]}..."
                )
                if "invalid" in key_value:
                    raise ValueError(f"Invalid key format for {kid}")
                return JWK(
                    kty="RSA",
                    use="sig",
                    kid=kid,
                    alg="RS256",
                    n="formatted-modulus",
                    e="AQAB",
                )

            with patch(
                "app.utils.jwt_keys.format_public_key_to_jwk",
                side_effect=mock_format_key,
            ):
                import httpx

                transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=True)
                async with httpx.AsyncClient(
                    transport=transport, base_url="http://test"
                ) as ac:
                    resp = await ac.get("/.well-known/jwks.json")

                    # Property: Always returns 200 OK
                    assert resp.status_code == 200

                    # Property: Always returns valid JSON
                    data = resp.json()
                    assert isinstance(data, dict)

                    # Property: Always has 'keys' field
                    assert "keys" in data
                    assert isinstance(data["keys"], list)

                    # Property: If cache hit with valid data, should return cached data
                    if cache_state and "invalid" not in cache_state:
                        assert len(data["keys"]) == 1
                        assert data["keys"][0]["kid"] == "cached-key"
                    else:
                        # Property: Should handle invalid keys gracefully
                        # Count valid keys that were successfully formatted
                        valid_keys = [k for k in key_set if "invalid" not in k.value]
                        if len(data["keys"]) != len(valid_keys):
                            print(
                                f"DEBUG: key_set={key_set}, valid_keys={valid_keys}, response={data}"
                            )
                        assert len(data["keys"]) == len(valid_keys)


@pytest.mark.asyncio
@settings(
    max_examples=10,
    deadline=5000,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)  # Reduced examples, added deadline
@given(cache_ttl=st.integers(min_value=1, max_value=3600))
async def test_jwks_cache_ttl_property_based(cache_ttl: int, monkeypatch):
    """Property-based test for JWKS cache TTL behavior."""
    from app.main import create_app

    # Create test app for this specific test
    test_app = create_app()

    # Mock Redis to verify TTL is set correctly
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.setex.return_value = True
    mock_redis.close.return_value = None

    # Patch the Configuration class attribute
    from app.core.config import Configuration

    # Create a custom config instance with the test TTL value
    original_init = Configuration.__init__

    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.JWKS_CACHE_TTL_SEC = cache_ttl

    monkeypatch.setattr(Configuration, "__init__", patched_init)

    with patch("app.api.endpoints.jwks._build_redis_client", return_value=mock_redis):
        import httpx

        transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=True)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/.well-known/jwks.json")

            # Property: Should always succeed
            assert resp.status_code == 200

            # Property: Should call setex with correct TTL
            mock_redis.setex.assert_called_once()
            call_args = mock_redis.setex.call_args
            assert call_args[0][1] == cache_ttl  # TTL should match configuration


@pytest.mark.asyncio
@settings(
    max_examples=10,
    deadline=5000,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)  # Reduced examples, added deadline
@given(
    error_type=st.sampled_from(
        ["redis_connection", "redis_get", "redis_set", "key_format"]
    )
)
async def test_jwks_error_handling_property_based(error_type: str):
    """Property-based test for JWKS error handling."""
    from app.main import create_app

    # Create test app for this specific test
    test_app = create_app()

    # Mock Redis to simulate different error conditions
    mock_redis = AsyncMock()

    if error_type == "redis_connection":
        # Simulate Redis connection failure
        mock_redis.get.side_effect = Exception("Redis connection failed")
    elif error_type == "redis_get":
        # Simulate Redis get failure
        mock_redis.get.side_effect = Exception("Redis get failed")
    elif error_type == "redis_set":
        # Simulate Redis set failure
        mock_redis.get.return_value = None
        mock_redis.setex.side_effect = Exception("Redis set failed")
    else:  # key_format
        # Simulate key formatting failure
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True

    with patch("app.api.endpoints.jwks._build_redis_client", return_value=mock_redis):
        if error_type == "key_format":
            # Mock key formatting to fail
            def mock_format_key_fail(key_value, kid):
                raise ValueError(f"Key formatting failed for {kid}")

            with patch(
                "app.utils.jwt_keys.format_public_key_to_jwk",
                side_effect=mock_format_key_fail,
            ):
                import httpx

                transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=True)
                async with httpx.AsyncClient(
                    transport=transport, base_url="http://test"
                ) as ac:
                    resp = await ac.get("/.well-known/jwks.json")

                    # Property: Should always return 200 even with errors
                    assert resp.status_code == 200
                    data = resp.json()
                    assert "keys" in data
                    # Should return empty keys list when formatting fails
                    assert len(data["keys"]) == 0
        else:
            import httpx

            transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=True)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://test"
            ) as ac:
                resp = await ac.get("/.well-known/jwks.json")

                # Property: Should always return 200 even with Redis errors
                assert resp.status_code == 200
                data = resp.json()
                assert "keys" in data
                # Should return empty keys list when Redis fails
                assert len(data["keys"]) == 0
