"""Unit tests for JWKS cache utilities."""
import json
from unittest.mock import AsyncMock, patch

import pytest

from app.domain.schemas.jwks import JWK, JWKSet
from app.utils.jwks_cache import (
    JWKS_CACHE_KEY,
    get_jwks_cache,
    invalidate_jwks_cache,
    set_jwks_cache,
)


@pytest.fixture
def mock_redis():
    """Create a mocked Redis client for testing."""
    return AsyncMock()


class TestGetJwksCache:
    """Test cache retrieval operations."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_jwks_cache_hit(self, mock_redis, sample_jwks):
        """Test successful cache retrieval."""
        # Mock Redis to return cached data
        cached_data = json.dumps(sample_jwks.model_dump())
        mock_redis.get.return_value = cached_data.encode()

        result = await get_jwks_cache(mock_redis)

        assert result is not None
        assert result.keys == sample_jwks.keys
        mock_redis.get.assert_called_once_with(JWKS_CACHE_KEY)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_jwks_cache_miss(self, mock_redis):
        """Test cache miss returns None."""
        mock_redis.get.return_value = None

        result = await get_jwks_cache(mock_redis)

        assert result is None
        mock_redis.get.assert_called_once_with(JWKS_CACHE_KEY)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_jwks_cache_redis_error(self, mock_redis):
        """Test graceful handling of Redis errors."""
        mock_redis.get.side_effect = Exception("Redis connection failed")

        result = await get_jwks_cache(mock_redis)

        assert result is None
        mock_redis.get.assert_called_once_with(JWKS_CACHE_KEY)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_jwks_cache_invalid_json(self, mock_redis):
        """Test graceful handling of invalid JSON in cache."""
        mock_redis.get.return_value = b"invalid json"

        result = await get_jwks_cache(mock_redis)

        assert result is None
        mock_redis.get.assert_called_once_with(JWKS_CACHE_KEY)


class TestSetJwksCache:
    """Test cache storage operations."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_set_jwks_cache_success(self, mock_redis, sample_jwks):
        """Test successful cache storage."""
        mock_redis.setex.return_value = True

        result = await set_jwks_cache(mock_redis, sample_jwks)

        assert result is True
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == JWKS_CACHE_KEY
        assert call_args[0][1] == 3600  # Default TTL from settings
        # Verify the serialized data is valid JSON
        stored_data = json.loads(call_args[0][2])
        assert stored_data["keys"] == sample_jwks.model_dump()["keys"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_set_jwks_cache_redis_error(self, mock_redis, sample_jwks):
        """Test graceful handling of Redis storage errors."""
        mock_redis.setex.side_effect = Exception("Redis storage failed")

        result = await set_jwks_cache(mock_redis, sample_jwks)

        assert result is False
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_set_jwks_cache_serialization_error(self, mock_redis):
        """Test handling of JWKSet serialization errors."""
        # Create a valid JWKSet but mock json.dumps to fail
        valid_jwk = JWK(
            kty="RSA",
            use="sig",
            kid="test-key-1",
            alg="RS256",
            n="test-modulus",
            e="AQAB",
        )
        valid_jwks = JWKSet(keys=[valid_jwk])

        # Mock json.dumps to raise an exception
        with patch(
            "app.utils.jwks_cache.json.dumps",
            side_effect=Exception("JSON serialization failed"),
        ):
            result = await set_jwks_cache(mock_redis, valid_jwks)

        assert result is False
        # Should not call Redis if serialization fails
        mock_redis.setex.assert_not_called()


class TestInvalidateJwksCache:
    """Test cache invalidation operations."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_invalidate_jwks_cache_success(self, mock_redis):
        """Test successful cache invalidation."""
        mock_redis.delete.return_value = 1

        result = await invalidate_jwks_cache(mock_redis)

        assert result is True
        mock_redis.delete.assert_called_once_with(JWKS_CACHE_KEY)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_invalidate_jwks_cache_redis_error(self, mock_redis):
        """Test graceful handling of Redis deletion errors."""
        mock_redis.delete.side_effect = Exception("Redis deletion failed")

        result = await invalidate_jwks_cache(mock_redis)

        assert result is False
        mock_redis.delete.assert_called_once_with(JWKS_CACHE_KEY)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_invalidate_jwks_cache_key_not_found(self, mock_redis):
        """Test invalidation when key doesn't exist."""
        mock_redis.delete.return_value = 0

        result = await invalidate_jwks_cache(mock_redis)

        # When the cache key is not found, the operation should return *False*
        # to indicate that no deletion occurred.  This matches the behaviour
        # asserted by the integration tests in
        # *tests/integration/api/test_jwks_metrics.py*.
        assert result is False
        mock_redis.delete.assert_called_once_with(JWKS_CACHE_KEY)


class TestRedisClientBuilder:
    """Test Redis client creation."""

    @patch("app.utils.jwks_cache.Redis")
    @pytest.mark.unit
    def test_build_redis_client(self, mock_redis_class):
        """Test Redis client creation with correct URL."""
        from app.utils import jwks_cache

        jwks_cache._redis_singleton = None

        jwks_cache._build_redis_client()

        # Expect test Redis URL from pytest.ini
        mock_redis_class.from_url.assert_called_once_with("redis://localhost:6379/15")


class TestInvalidateJwksCacheSync:
    """Tests for the synchronous cache invalidation wrapper."""

    @pytest.mark.unit
    def test_sync_invalidation_success(self, monkeypatch):
        redis_client = AsyncMock()
        monkeypatch.setattr(
            "app.utils.jwks_cache._build_redis_client", lambda: redis_client
        )
        calls = []

        import asyncio
        import inspect  # Local import to avoid polluting global namespace

        def fake_run(coro):
            """A lightweight replacement for ``asyncio.run`` used in tests.

            It **executes** coroutine objects to completion so that they do not
            generate "coroutine was never awaited" warnings while still
            allowing the test to spy on how many times it was invoked.
            """

            calls.append(coro)

            # Only execute coroutine objects – ``redis.close()`` and similar are
            # also coroutines.  For non coroutine inputs (e.g. already executed
            # results) simply return the value as-is.
            if inspect.iscoroutine(coro):
                loop = asyncio.new_event_loop()
                try:
                    return loop.run_until_complete(coro)
                finally:
                    loop.close()

            return coro

        monkeypatch.setattr("app.utils.jwks_cache.asyncio.run", fake_run)

        monkeypatch.setattr(
            "app.utils.jwks_cache.invalidate_jwks_cache", AsyncMock(return_value=True)
        )

        from app.utils.jwks_cache import invalidate_jwks_cache_sync

        assert invalidate_jwks_cache_sync() is True
        assert len(calls) == 2

    @pytest.mark.unit
    def test_sync_invalidation_failure(self, monkeypatch):
        monkeypatch.setattr(
            "app.utils.jwks_cache._build_redis_client", lambda: AsyncMock()
        )

        import asyncio
        import inspect

        def fake_run(coro):
            """Simulate a failure in ``asyncio.run`` while avoiding unawaited warnings."""

            # Close coroutine to prevent RuntimeWarning about it being unawaited
            if inspect.iscoroutine(coro):
                coro.close()

            raise RuntimeError("boom")

        monkeypatch.setattr("app.utils.jwks_cache.asyncio.run", fake_run)

        from app.utils.jwks_cache import invalidate_jwks_cache_sync

        assert invalidate_jwks_cache_sync() is False
