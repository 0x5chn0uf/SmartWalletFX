"""Unit tests for JWKS cache utilities."""
import json
from unittest.mock import AsyncMock, patch

import pytest

from app.core.config import Configuration
from app.domain.schemas.jwks import JWK, JWKSet
from app.utils.jwks_cache import JWKS_CACHE_KEY, JWKSCacheUtils


@pytest.fixture
def mock_redis():
    """Create a mocked Redis client for testing."""
    return AsyncMock()


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = _MockConfig()
    config.redis_url = "redis://localhost:6379/15"
    config.JWKS_CACHE_TTL_SEC = 3600
    return config


@pytest.fixture
def jwks_cache_utils(mock_config):
    """Create JWKSCacheUtils instance."""
    return JWKSCacheUtils(mock_config)


class _MockConfig:
    """Mock config for testing."""

    def __init__(self):
        self.redis_url = "redis://localhost:6379/15"
        self.JWKS_CACHE_TTL_SEC = 3600


class TestJWKSCacheUtils:
    """Test JWKSCacheUtils class functionality."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_jwks_cache_hit(self, mock_redis, sample_jwks, jwks_cache_utils):
        """Test successful cache retrieval."""
        # Mock Redis to return cached data
        cached_data = json.dumps(sample_jwks.model_dump())
        mock_redis.get.return_value = cached_data.encode()

        result = await jwks_cache_utils.get_jwks_cache(mock_redis)

        assert result is not None
        assert result.keys == sample_jwks.keys
        mock_redis.get.assert_called_once_with(JWKS_CACHE_KEY)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_jwks_cache_miss(self, mock_redis, jwks_cache_utils):
        """Test cache miss returns None."""
        mock_redis.get.return_value = None

        result = await jwks_cache_utils.get_jwks_cache(mock_redis)

        assert result is None
        mock_redis.get.assert_called_once_with(JWKS_CACHE_KEY)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_jwks_cache_redis_error(self, mock_redis, jwks_cache_utils):
        """Test graceful handling of Redis errors."""
        mock_redis.get.side_effect = Exception("Redis connection failed")

        result = await jwks_cache_utils.get_jwks_cache(mock_redis)

        assert result is None
        mock_redis.get.assert_called_once_with(JWKS_CACHE_KEY)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_jwks_cache_invalid_json(self, mock_redis, jwks_cache_utils):
        """Test graceful handling of invalid JSON in cache."""
        mock_redis.get.return_value = b"invalid json"

        result = await jwks_cache_utils.get_jwks_cache(mock_redis)

        assert result is None
        mock_redis.get.assert_called_once_with(JWKS_CACHE_KEY)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_set_jwks_cache_success(
        self, mock_redis, sample_jwks, jwks_cache_utils
    ):
        """Test successful cache storage."""
        mock_redis.setex.return_value = True

        result = await jwks_cache_utils.set_jwks_cache(mock_redis, sample_jwks)

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
    async def test_set_jwks_cache_redis_error(
        self, mock_redis, sample_jwks, jwks_cache_utils
    ):
        """Test graceful handling of Redis storage errors."""
        mock_redis.setex.side_effect = Exception("Redis storage failed")

        result = await jwks_cache_utils.set_jwks_cache(mock_redis, sample_jwks)

        assert result is False
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_set_jwks_cache_serialization_error(
        self, mock_redis, jwks_cache_utils
    ):
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
            result = await jwks_cache_utils.set_jwks_cache(mock_redis, valid_jwks)

        assert result is False
        # Should not call Redis if serialization fails
        mock_redis.setex.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_invalidate_jwks_cache_success(self, mock_redis, jwks_cache_utils):
        """Test successful cache invalidation."""
        mock_redis.delete.return_value = 1

        result = await jwks_cache_utils.invalidate_jwks_cache(mock_redis)

        assert result is True
        mock_redis.delete.assert_called_once_with(JWKS_CACHE_KEY)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_invalidate_jwks_cache_redis_error(
        self, mock_redis, jwks_cache_utils
    ):
        """Test graceful handling of Redis deletion errors."""
        mock_redis.delete.side_effect = Exception("Redis deletion failed")

        result = await jwks_cache_utils.invalidate_jwks_cache(mock_redis)

        assert result is False
        mock_redis.delete.assert_called_once_with(JWKS_CACHE_KEY)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_invalidate_jwks_cache_key_not_found(
        self, mock_redis, jwks_cache_utils
    ):
        """Test invalidation when key doesn't exist."""
        mock_redis.delete.return_value = 0

        result = await jwks_cache_utils.invalidate_jwks_cache(mock_redis)

        # When the cache key is not found, the operation should return *False*
        # to indicate that no deletion occurred.  This matches the behaviour
        # asserted by the integration tests in
        # *tests/integration/api/test_jwks_metrics.py*.
        assert result is False
        mock_redis.delete.assert_called_once_with(JWKS_CACHE_KEY)

    @patch("app.utils.jwks_cache.Redis")
    @pytest.mark.unit
    def test_build_redis_client(self, mock_redis_class, mock_config):
        """Test Redis client creation with correct URL."""
        jwks_cache_utils = JWKSCacheUtils(mock_config)

        jwks_cache_utils._build_redis_client()

        # Should create Redis client with config URL
        mock_redis_class.from_url.assert_called_once_with("redis://localhost:6379/15")

    @pytest.mark.unit
    def test_sync_invalidation_success(self, mock_config):
        """Test synchronous cache invalidation."""
        jwks_cache_utils = JWKSCacheUtils(mock_config)

        with patch.object(
            jwks_cache_utils, "_build_redis_client"
        ) as mock_build_client, patch("asyncio.run") as mock_asyncio_run:
            mock_redis = AsyncMock()
            mock_build_client.return_value = mock_redis
            mock_asyncio_run.return_value = True

            result = jwks_cache_utils.invalidate_jwks_cache_sync()

            assert result is True
            # Should have called asyncio.run twice (invalidate + close)
            assert mock_asyncio_run.call_count == 2

    @pytest.mark.unit
    def test_sync_invalidation_failure(self, mock_config):
        """Test synchronous cache invalidation failure."""
        jwks_cache_utils = JWKSCacheUtils(mock_config)

        with patch.object(
            jwks_cache_utils, "_build_redis_client"
        ) as mock_build_client, patch("asyncio.run") as mock_asyncio_run:
            mock_redis = AsyncMock()
            mock_build_client.return_value = mock_redis
            mock_asyncio_run.side_effect = RuntimeError("boom")

            result = jwks_cache_utils.invalidate_jwks_cache_sync()

            assert result is False
