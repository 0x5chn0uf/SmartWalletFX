"""
Unit tests for DeFi aggregation service.
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from app.models.aggregate_metrics import AggregateMetricsModel
from app.services.defi_aggregation_service import DeFiAggregationService


class TestDeFiAggregationService:
    """Test cases for DeFiAggregationService."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        return Mock()

    @pytest.fixture
    def mock_metrics_repo(self):
        """Mock aggregate metrics repository."""
        return Mock()

    @pytest.fixture
    def mock_position_adapter(self):
        """Mock DeFi position adapter."""
        return Mock()

    @pytest.fixture
    def aggregation_service(self, mock_db, mock_redis):
        """DeFi aggregation service instance."""
        service = DeFiAggregationService(mock_db, mock_redis)
        service.metrics_repo = Mock()
        service.position_adapter = Mock()
        return service

    @pytest.fixture
    def sample_positions(self):
        """Sample DeFi positions for testing."""
        return [
            {
                "protocol": "aave",
                "asset": "USDC",
                "amount": 1000.0,
                "usd_value": 1000.0,
                "apy": 0.05,
                "type": "supply",
            },
            {
                "protocol": "compound",
                "asset": "ETH",
                "amount": 5.0,
                "usd_value": 10000.0,
                "apy": 0.08,
                "type": "supply",
            },
            {
                "protocol": "aave",
                "asset": "USDT",
                "amount": 500.0,
                "usd_value": 500.0,
                "apy": 0.03,
                "type": "borrowing",
            },
        ]

    @pytest.fixture
    def sample_metrics_model(self):
        """Sample AggregateMetricsModel instance."""
        return AggregateMetricsModel.create_new("0x1234567890abcdef")

    @pytest.mark.asyncio
    async def test_aggregate_wallet_positions_cache_hit(
        self, aggregation_service, sample_metrics_model
    ):
        """Test aggregation with cache hit."""
        # Mock cache hit
        aggregation_service._get_cached_metrics = AsyncMock(
            return_value=sample_metrics_model
        )

        result = await aggregation_service.aggregate_wallet_positions(
            "0x1234567890abcdef"
        )

        assert result == sample_metrics_model
        aggregation_service._get_cached_metrics.assert_called_once_with(
            "0x1234567890abcdef"
        )

    @pytest.mark.asyncio
    async def test_aggregate_wallet_positions_success(
        self, aggregation_service, sample_positions, sample_metrics_model
    ):
        """Test successful aggregation without cache."""
        # Mock cache miss
        aggregation_service._get_cached_metrics = AsyncMock(return_value=None)
        # Mock position fetching
        aggregation_service.position_adapter.fetch_positions = AsyncMock(
            return_value=sample_positions
        )
        # Mock metrics creation
        aggregation_service._get_or_create_metrics = AsyncMock(
            return_value=sample_metrics_model
        )
        # Mock repository operations
        aggregation_service.metrics_repo.upsert = AsyncMock()
        # Mock caching
        aggregation_service._cache_metrics = AsyncMock()

        result = await aggregation_service.aggregate_wallet_positions(
            "0x1234567890abcdef"
        )

        assert result == sample_metrics_model
        aggregation_service.position_adapter.fetch_positions.assert_called_once_with(
            "0x1234567890abcdef"
        )
        aggregation_service.metrics_repo.upsert.assert_called_once_with(
            sample_metrics_model
        )
        aggregation_service._cache_metrics.assert_called_once_with(
            "0x1234567890abcdef", sample_metrics_model
        )

    @pytest.mark.asyncio
    async def test_aggregate_wallet_positions_error_handling(self, aggregation_service):
        """Test error handling during aggregation."""
        # Mock cache miss
        aggregation_service._get_cached_metrics = AsyncMock(return_value=None)
        # Mock position fetching to raise exception
        aggregation_service.position_adapter.fetch_positions = AsyncMock(
            side_effect=Exception("Network error")
        )
        # Mock metrics creation
        sample_metrics_model = AggregateMetricsModel.create_new("0x1234567890abcdef")
        aggregation_service._get_or_create_metrics = AsyncMock(
            return_value=sample_metrics_model
        )

        result = await aggregation_service.aggregate_wallet_positions(
            "0x1234567890abcdef"
        )

        assert result == sample_metrics_model
        aggregation_service._get_or_create_metrics.assert_called_once_with(
            "0x1234567890abcdef"
        )

    @pytest.mark.asyncio
    async def test_get_wallet_metrics(self, aggregation_service, sample_metrics_model):
        """Test getting wallet metrics."""
        aggregation_service.metrics_repo.get_latest = AsyncMock(
            return_value=sample_metrics_model
        )

        result = await aggregation_service.get_wallet_metrics("0x1234567890abcdef")

        assert result == sample_metrics_model
        aggregation_service.metrics_repo.get_latest.assert_called_once_with(
            "0x1234567890abcdef"
        )

    @pytest.mark.asyncio
    async def test_get_wallet_metrics_not_found(self, aggregation_service):
        """Test getting wallet metrics when not found."""
        aggregation_service.metrics_repo.get_latest = AsyncMock(return_value=None)

        result = await aggregation_service.get_wallet_metrics("0x1234567890abcdef")

        assert result is None
        aggregation_service.metrics_repo.get_latest.assert_called_once_with(
            "0x1234567890abcdef"
        )

    @pytest.mark.asyncio
    async def test_get_wallet_history(self, aggregation_service):
        """Test getting wallet history."""
        history_metrics = [
            AggregateMetricsModel.create_new("0x1234567890abcdef"),
            AggregateMetricsModel.create_new("0x1234567890abcdef"),
        ]
        aggregation_service.metrics_repo.get_history = AsyncMock(
            return_value=history_metrics
        )

        result = await aggregation_service.get_wallet_history(
            "0x1234567890abcdef", limit=50, offset=10
        )

        assert result == history_metrics
        aggregation_service.metrics_repo.get_history.assert_called_once_with(
            "0x1234567890abcdef", 50, 10
        )

    @pytest.mark.asyncio
    async def test_refresh_wallet_metrics(
        self, aggregation_service, sample_metrics_model
    ):
        """Test refreshing wallet metrics."""
        # Mock cache clearing
        aggregation_service._clear_cache = AsyncMock()
        # Mock aggregation
        aggregation_service.aggregate_wallet_positions = AsyncMock(
            return_value=sample_metrics_model
        )

        result = await aggregation_service.refresh_wallet_metrics("0x1234567890abcdef")

        assert result == sample_metrics_model
        aggregation_service._clear_cache.assert_called_once_with("0x1234567890abcdef")
        aggregation_service.aggregate_wallet_positions.assert_called_once_with(
            "0x1234567890abcdef"
        )

    @pytest.mark.asyncio
    async def test_get_or_create_metrics_existing(
        self, aggregation_service, sample_metrics_model
    ):
        """Test getting existing metrics."""
        aggregation_service.metrics_repo.get_latest = AsyncMock(
            return_value=sample_metrics_model
        )

        result = await aggregation_service._get_or_create_metrics("0x1234567890abcdef")

        assert result == sample_metrics_model
        aggregation_service.metrics_repo.get_latest.assert_called_once_with(
            "0x1234567890abcdef"
        )

    @pytest.mark.asyncio
    async def test_get_or_create_metrics_new(self, aggregation_service):
        """Test creating new metrics."""
        aggregation_service.metrics_repo.get_latest = AsyncMock(return_value=None)

        result = await aggregation_service._get_or_create_metrics("0x1234567890abcdef")

        assert isinstance(result, AggregateMetricsModel)
        assert result.wallet_id == "0x1234567890abcdef"
        aggregation_service.metrics_repo.get_latest.assert_called_once_with(
            "0x1234567890abcdef"
        )

    @pytest.mark.asyncio
    async def test_get_cached_metrics_no_redis(self, aggregation_service):
        """Test cache retrieval when Redis is not available."""
        aggregation_service.redis = None

        result = await aggregation_service._get_cached_metrics("0x1234567890abcdef")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_cached_metrics_success(self, aggregation_service):
        """Test successful cache retrieval."""
        cache_data = {
            "id": 1,
            "tvl": 10000.0,
            "total_borrowings": 2000.0,
            "aggregate_apy": 0.08,
            "positions": [{"protocol": "aave", "asset": "USDC"}],
            "as_of": "2023-01-01T00:00:00",
        }
        aggregation_service.redis.get = AsyncMock(return_value=json.dumps(cache_data))

        result = await aggregation_service._get_cached_metrics("0x1234567890abcdef")

        assert result is not None
        assert isinstance(result, AggregateMetricsModel)
        assert result.tvl == 10000.0
        assert result.total_borrowings == 2000.0
        assert result.aggregate_apy == 0.08
        aggregation_service.redis.get.assert_called_once_with(
            "defi:aggregate:0x1234567890abcdef"
        )

    @pytest.mark.asyncio
    async def test_get_cached_metrics_not_found(self, aggregation_service):
        """Test cache retrieval when key not found."""
        aggregation_service.redis.get = AsyncMock(return_value=None)

        result = await aggregation_service._get_cached_metrics("0x1234567890abcdef")

        assert result is None
        aggregation_service.redis.get.assert_called_once_with(
            "defi:aggregate:0x1234567890abcdef"
        )

    @pytest.mark.asyncio
    async def test_get_cached_metrics_invalid_json(self, aggregation_service):
        """Test cache retrieval with invalid JSON."""
        aggregation_service.redis.get = AsyncMock(return_value="invalid json")

        result = await aggregation_service._get_cached_metrics("0x1234567890abcdef")

        assert result is None
        aggregation_service.redis.get.assert_called_once_with(
            "defi:aggregate:0x1234567890abcdef"
        )

    @pytest.mark.asyncio
    async def test_get_cached_metrics_redis_exception(self, aggregation_service):
        """Test cache retrieval when Redis raises exception."""
        aggregation_service.redis.get = AsyncMock(side_effect=Exception("Redis error"))

        result = await aggregation_service._get_cached_metrics("0x1234567890abcdef")

        assert result is None
        aggregation_service.redis.get.assert_called_once_with(
            "defi:aggregate:0x1234567890abcdef"
        )

    @pytest.mark.asyncio
    async def test_cache_metrics_no_redis(
        self, aggregation_service, sample_metrics_model
    ):
        """Test caching when Redis is not available."""
        aggregation_service.redis = None

        await aggregation_service._cache_metrics(
            "0x1234567890abcdef", sample_metrics_model
        )

        # Should not raise any exception

    @pytest.mark.asyncio
    async def test_cache_metrics_success(
        self, aggregation_service, sample_metrics_model
    ):
        """Test successful caching."""
        aggregation_service.redis.setex = AsyncMock()

        await aggregation_service._cache_metrics(
            "0x1234567890abcdef", sample_metrics_model
        )

        aggregation_service.redis.setex.assert_called_once()
        call_args = aggregation_service.redis.setex.call_args
        assert call_args[0][0] == "defi:aggregate:0x1234567890abcdef"  # key
        assert call_args[0][1] == 300  # TTL
        # Verify JSON is valid
        json.loads(call_args[0][2])

    @pytest.mark.asyncio
    async def test_cache_metrics_redis_exception(
        self, aggregation_service, sample_metrics_model
    ):
        """Test caching when Redis raises exception."""
        aggregation_service.redis.setex = AsyncMock(
            side_effect=Exception("Redis error")
        )

        await aggregation_service._cache_metrics(
            "0x1234567890abcdef", sample_metrics_model
        )

        # Should not raise any exception
        aggregation_service.redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_cache_no_redis(self, aggregation_service):
        """Test cache clearing when Redis is not available."""
        aggregation_service.redis = None

        await aggregation_service._clear_cache("0x1234567890abcdef")

        # Should not raise any exception

    @pytest.mark.asyncio
    async def test_clear_cache_success(self, aggregation_service):
        """Test successful cache clearing."""
        aggregation_service.redis.delete = AsyncMock()

        await aggregation_service._clear_cache("0x1234567890abcdef")

        aggregation_service.redis.delete.assert_called_once_with(
            "defi:aggregate:0x1234567890abcdef"
        )

    @pytest.mark.asyncio
    async def test_clear_cache_redis_exception(self, aggregation_service):
        """Test cache clearing when Redis raises exception."""
        aggregation_service.redis.delete = AsyncMock(
            side_effect=Exception("Redis error")
        )

        await aggregation_service._clear_cache("0x1234567890abcdef")

        # Should not raise any exception
        aggregation_service.redis.delete.assert_called_once()

    def test_validate_ethereum_address_valid(self, aggregation_service):
        """Test valid Ethereum address validation."""
        valid_addresses = [
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            "0x1234567890abcdef1234567890abcdef12345678",
            "0xABCDEF1234567890ABCDEF1234567890ABCDEF12",
        ]

        for address in valid_addresses:
            assert aggregation_service.validate_ethereum_address(address) is True

    def test_validate_ethereum_address_invalid(self, aggregation_service):
        """Test invalid Ethereum address validation."""
        invalid_addresses = [
            None,
            "",
            "0x123",  # Too short
            "0x1234567890abcdef1234567890abcdef123456789",  # Too long
            "0x1234567890abcdef1234567890abcdef1234567g",  # Invalid hex
            "1234567890abcdef1234567890abcdef12345678",  # No 0x prefix
            "0X1234567890abcdef1234567890abcdef12345678",  # Wrong prefix case
        ]

        for address in invalid_addresses:
            assert aggregation_service.validate_ethereum_address(address) is False

    @pytest.mark.asyncio
    async def test_aggregate_wallet_positions_with_borrowing_positions(
        self, aggregation_service, sample_metrics_model
    ):
        """Test aggregation with borrowing positions."""
        positions = [
            {
                "protocol": "aave",
                "asset": "USDC",
                "amount": 1000.0,
                "usd_value": 1000.0,
                "apy": 0.05,
                "type": "supply",
            },
            {
                "protocol": "compound",
                "asset": "USDT",
                "amount": 500.0,
                "usd_value": 500.0,
                "apy": 0.03,
                "type": "borrowing",
            },
        ]

        # Mock cache miss
        aggregation_service._get_cached_metrics = AsyncMock(return_value=None)
        # Mock position fetching
        aggregation_service.position_adapter.fetch_positions = AsyncMock(
            return_value=positions
        )
        # Mock metrics creation
        aggregation_service._get_or_create_metrics = AsyncMock(
            return_value=sample_metrics_model
        )
        # Mock repository operations
        aggregation_service.metrics_repo.upsert = AsyncMock()
        # Mock caching
        aggregation_service._cache_metrics = AsyncMock()

        result = await aggregation_service.aggregate_wallet_positions(
            "0x1234567890abcdef"
        )

        assert result == sample_metrics_model
        # Verify that borrowing positions were tracked
        assert sample_metrics_model.total_borrowings == 500.0

    @pytest.mark.asyncio
    async def test_aggregate_wallet_positions_empty_positions(
        self, aggregation_service, sample_metrics_model
    ):
        """Test aggregation with empty positions."""
        # Mock cache miss
        aggregation_service._get_cached_metrics = AsyncMock(return_value=None)
        # Mock position fetching to return empty list
        aggregation_service.position_adapter.fetch_positions = AsyncMock(
            return_value=[]
        )
        # Mock metrics creation
        aggregation_service._get_or_create_metrics = AsyncMock(
            return_value=sample_metrics_model
        )
        # Mock repository operations
        aggregation_service.metrics_repo.upsert = AsyncMock()
        # Mock caching
        aggregation_service._cache_metrics = AsyncMock()

        result = await aggregation_service.aggregate_wallet_positions(
            "0x1234567890abcdef"
        )

        assert result == sample_metrics_model
        # Verify metrics were reset
        assert sample_metrics_model.positions == []
        assert sample_metrics_model.tvl == 0.0
        assert sample_metrics_model.total_borrowings == 0.0

    @pytest.mark.asyncio
    async def test_get_cached_metrics_with_as_of_timestamp(self, aggregation_service):
        """Test cache retrieval with as_of timestamp."""
        cache_data = {
            "id": 1,
            "tvl": 10000.0,
            "total_borrowings": 2000.0,
            "aggregate_apy": 0.08,
            "positions": [],
            "as_of": "2023-01-01T12:00:00",
        }
        aggregation_service.redis.get = AsyncMock(return_value=json.dumps(cache_data))

        result = await aggregation_service._get_cached_metrics("0x1234567890abcdef")

        assert result is not None
        assert isinstance(result.as_of, datetime)
        assert result.as_of.year == 2023
        assert result.as_of.month == 1
        assert result.as_of.day == 1

    @pytest.mark.asyncio
    async def test_get_cached_metrics_without_as_of_timestamp(
        self, aggregation_service
    ):
        """Test cache retrieval without as_of timestamp."""
        cache_data = {
            "id": 1,
            "tvl": 10000.0,
            "total_borrowings": 2000.0,
            "aggregate_apy": 0.08,
            "positions": [],
        }
        aggregation_service.redis.get = AsyncMock(return_value=json.dumps(cache_data))

        result = await aggregation_service._get_cached_metrics("0x1234567890abcdef")

        assert result is not None
        assert isinstance(result.as_of, datetime)
