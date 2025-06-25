"""
Unit tests for metrics_cache module.
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest
from redis.asyncio import Redis

from app.domain.defi_tracker.schemas import AggregateMetricsSchema
from app.utils.metrics_cache import get_metrics_cache, set_metrics_cache


class TestMetricsCache:
    """Test cases for metrics cache functions."""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        return Mock(spec=Redis)

    @pytest.fixture
    def sample_metrics_data(self):
        """Sample metrics data for testing."""
        return {
            "id": "12345678-1234-5678-9abc-123456789abc",
            "wallet_id": "0x1234567890abcdef1234567890abcdef12345678",
            "tvl": 10000.0,
            "total_borrowings": 2000.0,
            "aggregate_apy": 0.08,
            "as_of": "2023-01-01T00:00:00",
            "positions": [
                {
                    "protocol": "aave",
                    "asset": "USDC",
                    "amount": 1000.0,
                    "usd_value": 1000.0,
                    "apy": 0.05,
                }
            ],
        }

    @pytest.fixture
    def sample_metrics_schema(self, sample_metrics_data):
        """Sample AggregateMetricsSchema instance."""
        return AggregateMetricsSchema(**sample_metrics_data)

    @pytest.mark.asyncio
    async def test_get_metrics_cache_success(self, mock_redis, sample_metrics_data):
        """Test successful cache retrieval."""
        # Mock Redis get to return JSON string
        mock_redis.get = AsyncMock(return_value=json.dumps(sample_metrics_data))

        result = await get_metrics_cache(mock_redis, "0x1234567890abcdef")

        assert result is not None
        assert isinstance(result, AggregateMetricsSchema)
        assert result.tvl == 10000.0
        assert result.total_borrowings == 2000.0
        assert result.aggregate_apy == 0.08
        assert len(result.positions) == 1

        # Verify Redis was called with correct key
        mock_redis.get.assert_called_once_with("defi:agg:0x1234567890abcdef")

    @pytest.mark.asyncio
    async def test_get_metrics_cache_bytes_response(
        self, mock_redis, sample_metrics_data
    ):
        """Test cache retrieval with bytes response from Redis."""
        # Mock Redis get to return bytes
        mock_redis.get = AsyncMock(
            return_value=json.dumps(sample_metrics_data).encode("utf-8")
        )

        result = await get_metrics_cache(mock_redis, "0x1234567890abcdef")

        assert result is not None
        assert isinstance(result, AggregateMetricsSchema)
        assert result.tvl == 10000.0

    @pytest.mark.asyncio
    async def test_get_metrics_cache_not_found(self, mock_redis):
        """Test cache retrieval when key not found."""
        # Mock Redis get to return None
        mock_redis.get = AsyncMock(return_value=None)

        result = await get_metrics_cache(mock_redis, "0x1234567890abcdef")

        assert result is None
        mock_redis.get.assert_called_once_with("defi:agg:0x1234567890abcdef")

    @pytest.mark.asyncio
    async def test_get_metrics_cache_invalid_json(self, mock_redis):
        """Test cache retrieval with invalid JSON."""
        # Mock Redis get to return invalid JSON
        mock_redis.get = AsyncMock(return_value="invalid json")

        result = await get_metrics_cache(mock_redis, "0x1234567890abcdef")

        assert result is None
        mock_redis.get.assert_called_once_with("defi:agg:0x1234567890abcdef")

    @pytest.mark.asyncio
    async def test_get_metrics_cache_redis_exception(self, mock_redis):
        """Test cache retrieval when Redis raises exception."""
        # Mock Redis get to raise exception
        mock_redis.get = AsyncMock(side_effect=Exception("Redis connection error"))

        result = await get_metrics_cache(mock_redis, "0x1234567890abcdef")

        assert result is None
        mock_redis.get.assert_called_once_with("defi:agg:0x1234567890abcdef")

    @pytest.mark.asyncio
    async def test_get_metrics_cache_address_normalization(
        self, mock_redis, sample_metrics_data
    ):
        """Test that wallet address is normalized to lowercase."""
        # Mock Redis get to return JSON string
        mock_redis.get = AsyncMock(return_value=json.dumps(sample_metrics_data))

        await get_metrics_cache(mock_redis, "0xABCDEF1234567890")

        # Verify Redis was called with lowercase key
        mock_redis.get.assert_called_once_with("defi:agg:0xabcdef1234567890")

    @pytest.mark.asyncio
    async def test_set_metrics_cache_success(self, mock_redis, sample_metrics_schema):
        """Test successful cache storage."""
        # Mock Redis setex
        mock_redis.setex = AsyncMock()

        result = await set_metrics_cache(
            mock_redis, "0x1234567890abcdef", sample_metrics_schema
        )

        assert result is True
        mock_redis.setex.assert_called_once()

        # Verify the call arguments
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "defi:agg:0x1234567890abcdef"  # key
        assert call_args[0][1] == 60  # default TTL

        # Verify the stored JSON is valid
        stored_json = call_args[0][2]
        parsed_data = json.loads(stored_json)
        assert parsed_data["tvl"] == 10000.0
        assert parsed_data["total_borrowings"] == 2000.0

    @pytest.mark.asyncio
    async def test_set_metrics_cache_custom_ttl(
        self, mock_redis, sample_metrics_schema
    ):
        """Test cache storage with custom TTL."""
        # Mock Redis setex
        mock_redis.setex = AsyncMock()

        result = await set_metrics_cache(
            mock_redis, "0x1234567890abcdef", sample_metrics_schema, ttl=300
        )

        assert result is True
        mock_redis.setex.assert_called_once()

        # Verify custom TTL was used
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 300  # custom TTL

    @pytest.mark.asyncio
    async def test_set_metrics_cache_redis_exception(
        self, mock_redis, sample_metrics_schema
    ):
        """Test cache storage when Redis raises exception."""
        # Mock Redis setex to raise exception
        mock_redis.setex = AsyncMock(side_effect=Exception("Redis connection error"))

        result = await set_metrics_cache(
            mock_redis, "0x1234567890abcdef", sample_metrics_schema
        )

        assert result is False
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_metrics_cache_address_normalization(
        self, mock_redis, sample_metrics_schema
    ):
        """Test that wallet address is normalized to lowercase when storing."""
        # Mock Redis setex
        mock_redis.setex = AsyncMock()

        await set_metrics_cache(mock_redis, "0xABCDEF1234567890", sample_metrics_schema)

        # Verify Redis was called with lowercase key
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "defi:agg:0xabcdef1234567890"

    @pytest.mark.asyncio
    async def test_set_metrics_cache_json_serialization(
        self, mock_redis, sample_metrics_schema
    ):
        """Test that metrics are properly serialized to JSON."""
        # Mock Redis setex
        mock_redis.setex = AsyncMock()

        await set_metrics_cache(mock_redis, "0x1234567890abcdef", sample_metrics_schema)

        # Verify the stored JSON contains all expected fields
        call_args = mock_redis.setex.call_args
        stored_json = call_args[0][2]
        parsed_data = json.loads(stored_json)

        # Check that all schema fields are present
        assert "tvl" in parsed_data
        assert "total_borrowings" in parsed_data
        assert "aggregate_apy" in parsed_data
        assert "positions" in parsed_data
        assert isinstance(parsed_data["positions"], list)

    @pytest.mark.asyncio
    async def test_get_metrics_cache_empty_positions(self, mock_redis):
        """Test cache retrieval with empty positions list."""
        metrics_data = {
            "id": "12345678-1234-5678-9abc-123456789abc",
            "wallet_id": "0x1234567890abcdef1234567890abcdef12345678",
            "tvl": 0.0,
            "total_borrowings": 0.0,
            "aggregate_apy": None,
            "as_of": "2023-01-01T00:00:00",
            "positions": [],
        }

        mock_redis.get = AsyncMock(return_value=json.dumps(metrics_data))

        result = await get_metrics_cache(mock_redis, "0x1234567890abcdef")

        assert result is not None
        assert isinstance(result, AggregateMetricsSchema)
        assert result.tvl == 0.0
        assert result.total_borrowings == 0.0
        assert result.aggregate_apy is None
        assert len(result.positions) == 0

    @pytest.mark.asyncio
    async def test_set_metrics_cache_complex_metrics(self, mock_redis):
        """Test cache storage with complex metrics data."""
        # Create complex metrics with multiple positions
        complex_metrics = AggregateMetricsSchema(
            id="12345678-1234-5678-9abc-123456789abc",
            wallet_id="0x1234567890abcdef1234567890abcdef12345678",
            tvl=50000.0,
            total_borrowings=15000.0,
            aggregate_apy=0.12,
            as_of=datetime.fromisoformat("2023-01-01T00:00:00"),
            positions=[
                {
                    "protocol": "aave",
                    "asset": "USDC",
                    "amount": 10000.0,
                    "usd_value": 10000.0,
                    "apy": 0.05,
                },
                {
                    "protocol": "compound",
                    "asset": "ETH",
                    "amount": 10.0,
                    "usd_value": 40000.0,
                    "apy": 0.15,
                },
            ],
        )

        mock_redis.setex = AsyncMock()

        result = await set_metrics_cache(
            mock_redis, "0x1234567890abcdef", complex_metrics
        )

        assert result is True

        # Verify the stored JSON contains complex data
        call_args = mock_redis.setex.call_args
        stored_json = call_args[0][2]
        parsed_data = json.loads(stored_json)

        assert parsed_data["tvl"] == 50000.0
        assert parsed_data["total_borrowings"] == 15000.0
        assert parsed_data["aggregate_apy"] == 0.12
        assert len(parsed_data["positions"]) == 2
        assert parsed_data["positions"][0]["protocol"] == "aave"
        assert parsed_data["positions"][1]["protocol"] == "compound"
