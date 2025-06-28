"""
Unit tests for DeFi Tracker repository interfaces.

Tests the abstract repository interfaces (ports) for persistence.
"""

import pytest

from app.domain.defi_tracker.entities import AggregateMetrics
from app.domain.defi_tracker.interfaces import AggregateMetricsRepository


class MockAggregateMetricsRepository(AggregateMetricsRepository):
    """Mock implementation of AggregateMetricsRepository for testing."""

    def __init__(self):
        self.metrics_store = {}
        self.history_store = {}

    async def upsert(self, metrics: AggregateMetrics) -> None:
        """Mock upsert implementation."""
        self.metrics_store[metrics.wallet_id] = metrics

    async def get_latest(self, wallet_id: str) -> AggregateMetrics | None:
        """Mock get_latest implementation."""
        return self.metrics_store.get(wallet_id)

    async def get_history(
        self, wallet_id: str, limit: int = 100, offset: int = 0
    ) -> list[AggregateMetrics]:
        """Mock get_history implementation."""
        history = self.history_store.get(wallet_id, [])
        return history[offset : offset + limit]


class TestAggregateMetricsRepository:
    """Test cases for AggregateMetricsRepository interface."""

    def test_aggregate_metrics_repository_is_abstract(self):
        """Test that AggregateMetricsRepository is an abstract base class."""
        with pytest.raises(TypeError):
            AggregateMetricsRepository()

    def test_aggregate_metrics_repository_has_required_methods(self):
        """Test that AggregateMetricsRepository has all required abstract methods."""
        # Check that the class has the required abstract methods
        assert hasattr(AggregateMetricsRepository, "upsert")
        assert hasattr(AggregateMetricsRepository, "get_latest")
        assert hasattr(AggregateMetricsRepository, "get_history")

        # Check that methods are abstract
        assert AggregateMetricsRepository.upsert.__isabstractmethod__
        assert AggregateMetricsRepository.get_latest.__isabstractmethod__
        assert AggregateMetricsRepository.get_history.__isabstractmethod__

    def test_mock_repository_implementation(self):
        """Test that our mock repository implements the interface correctly."""
        repo = MockAggregateMetricsRepository()

        # Verify it's an instance of the abstract class
        assert isinstance(repo, AggregateMetricsRepository)

        # Verify it has all required methods
        assert hasattr(repo, "upsert")
        assert hasattr(repo, "get_latest")
        assert hasattr(repo, "get_history")

        # Verify methods are callable
        assert callable(repo.upsert)
        assert callable(repo.get_latest)
        assert callable(repo.get_history)

    @pytest.mark.asyncio
    async def test_mock_repository_upsert_method(self):
        """Test the mock repository upsert method."""
        repo = MockAggregateMetricsRepository()
        wallet_id = "0x1234567890abcdef"

        # Create test metrics
        metrics = AggregateMetrics.new(wallet_id)
        metrics.tvl = 1000.0
        metrics.total_borrowings = 200.0

        # Test upsert
        await repo.upsert(metrics)

        # Verify metrics was stored
        assert wallet_id in repo.metrics_store
        assert repo.metrics_store[wallet_id] == metrics

    @pytest.mark.asyncio
    async def test_mock_repository_get_latest_method(self):
        """Test the mock repository get_latest method."""
        repo = MockAggregateMetricsRepository()
        wallet_id = "0x1234567890abcdef"

        # Test get_latest when no metrics exist
        result = await repo.get_latest(wallet_id)
        assert result is None

        # Create and store metrics
        metrics = AggregateMetrics.new(wallet_id)
        metrics.tvl = 1000.0
        await repo.upsert(metrics)

        # Test get_latest when metrics exist
        result = await repo.get_latest(wallet_id)
        assert result == metrics

    @pytest.mark.asyncio
    async def test_mock_repository_get_history_method(self):
        """Test the mock repository get_history method."""
        repo = MockAggregateMetricsRepository()
        wallet_id = "0x1234567890abcdef"

        # Test get_history when no history exists
        result = await repo.get_history(wallet_id)
        assert result == []

        # Create test history
        history = [
            AggregateMetrics.new(wallet_id),
            AggregateMetrics.new(wallet_id),
            AggregateMetrics.new(wallet_id),
        ]
        repo.history_store[wallet_id] = history

        # Test get_history with default parameters
        result = await repo.get_history(wallet_id)
        assert result == history

        # Test get_history with limit
        result = await repo.get_history(wallet_id, limit=2)
        assert len(result) == 2
        assert result == history[:2]

        # Test get_history with offset
        result = await repo.get_history(wallet_id, offset=1)
        assert len(result) == 2
        assert result == history[1:]

        # Test get_history with limit and offset
        result = await repo.get_history(wallet_id, limit=1, offset=1)
        assert len(result) == 1
        assert result == [history[1]]

    @pytest.mark.asyncio
    async def test_mock_repository_get_history_with_large_offset(self):
        """Test get_history with offset larger than available data."""
        repo = MockAggregateMetricsRepository()
        wallet_id = "0x1234567890abcdef"

        # Create test history
        history = [AggregateMetrics.new(wallet_id), AggregateMetrics.new(wallet_id)]
        repo.history_store[wallet_id] = history

        # Test with offset larger than available data
        result = await repo.get_history(wallet_id, offset=10)
        assert result == []

    @pytest.mark.asyncio
    async def test_mock_repository_get_history_with_zero_limit(self):
        """Test get_history with zero limit."""
        repo = MockAggregateMetricsRepository()
        wallet_id = "0x1234567890abcdef"

        # Create test history
        history = [AggregateMetrics.new(wallet_id), AggregateMetrics.new(wallet_id)]
        repo.history_store[wallet_id] = history

        # Test with zero limit
        result = await repo.get_history(wallet_id, limit=0)
        assert result == []

    @pytest.mark.asyncio
    async def test_mock_repository_get_history_with_negative_offset(self):
        """Test get_history with negative offset."""
        repo = MockAggregateMetricsRepository()
        wallet_id = "0x1234567890abcdef"

        # Create test history
        history = [AggregateMetrics.new(wallet_id), AggregateMetrics.new(wallet_id)]
        repo.history_store[wallet_id] = history

        # Test with negative offset (should return last item, per Python slicing)
        result = await repo.get_history(wallet_id, offset=-1)
        assert result == history[-1:]

    @pytest.mark.asyncio
    async def test_mock_repository_get_history_with_negative_limit(self):
        """Test get_history with negative limit."""
        repo = MockAggregateMetricsRepository()
        wallet_id = "0x1234567890abcdef"

        # Create test history
        history = [AggregateMetrics.new(wallet_id), AggregateMetrics.new(wallet_id)]
        repo.history_store[wallet_id] = history

        # Test with negative limit (should return all but last item, per Python slicing)
        result = await repo.get_history(wallet_id, limit=-1)
        assert result == history[:-1]

    @pytest.mark.asyncio
    async def test_mock_repository_multiple_wallets(self):
        """Test repository with multiple wallets."""
        repo = MockAggregateMetricsRepository()
        wallet_id_1 = "0x1234567890abcdef"
        wallet_id_2 = "0xfedcba0987654321"

        # Create metrics for first wallet
        metrics_1 = AggregateMetrics.new(wallet_id_1)
        metrics_1.tvl = 1000.0
        await repo.upsert(metrics_1)

        # Create metrics for second wallet
        metrics_2 = AggregateMetrics.new(wallet_id_2)
        metrics_2.tvl = 2000.0
        await repo.upsert(metrics_2)

        # Verify both wallets have their own data
        result_1 = await repo.get_latest(wallet_id_1)
        result_2 = await repo.get_latest(wallet_id_2)

        assert result_1 == metrics_1
        assert result_2 == metrics_2
        assert result_1 != result_2

    @pytest.mark.asyncio
    async def test_mock_repository_upsert_overwrites_existing(self):
        """Test that upsert overwrites existing metrics."""
        repo = MockAggregateMetricsRepository()
        wallet_id = "0x1234567890abcdef"

        # Create initial metrics
        metrics_1 = AggregateMetrics.new(wallet_id)
        metrics_1.tvl = 1000.0
        await repo.upsert(metrics_1)

        # Verify initial metrics
        result = await repo.get_latest(wallet_id)
        assert result == metrics_1

        # Create updated metrics
        metrics_2 = AggregateMetrics.new(wallet_id)
        metrics_2.tvl = 2000.0
        await repo.upsert(metrics_2)

        # Verify updated metrics
        result = await repo.get_latest(wallet_id)
        assert result == metrics_2
        assert result != metrics_1

    @pytest.mark.asyncio
    async def test_mock_repository_empty_wallet_id(self):
        """Test repository with empty wallet_id."""
        repo = MockAggregateMetricsRepository()
        wallet_id = ""

        # Create metrics with empty wallet_id
        metrics = AggregateMetrics.new(wallet_id)
        await repo.upsert(metrics)

        # Verify metrics can be retrieved
        result = await repo.get_latest(wallet_id)
        assert result == metrics

    @pytest.mark.asyncio
    async def test_mock_repository_special_characters_wallet_id(self):
        """Test repository with special characters in wallet_id."""
        repo = MockAggregateMetricsRepository()
        wallet_id = "0x1234567890abcdef!@#$%^&*()"

        # Create metrics with special characters in wallet_id
        metrics = AggregateMetrics.new(wallet_id)
        await repo.upsert(metrics)

        # Verify metrics can be retrieved
        result = await repo.get_latest(wallet_id)
        assert result == metrics

    @pytest.mark.asyncio
    async def test_mock_repository_large_history(self):
        """Test repository with large history."""
        repo = MockAggregateMetricsRepository()
        wallet_id = "0x1234567890abcdef"

        # Create large history
        history = [AggregateMetrics.new(wallet_id) for _ in range(1000)]
        repo.history_store[wallet_id] = history

        # Test with large limit
        result = await repo.get_history(wallet_id, limit=500)
        assert len(result) == 500
        assert result == history[:500]

        # Test with large offset
        result = await repo.get_history(wallet_id, offset=500)
        assert len(result) == 100
        assert result == history[500:600]

    def test_repository_method_signatures(self):
        """Test that repository methods have correct signatures."""
        # Check upsert signature
        upsert_sig = AggregateMetricsRepository.upsert.__annotations__
        assert "metrics" in upsert_sig
        assert (
            upsert_sig["metrics"] == "AggregateMetrics"
            or upsert_sig["metrics"] == AggregateMetrics
        )
        assert upsert_sig["return"] is type(None) or upsert_sig["return"] == "None"

        # Check get_latest signature
        get_latest_sig = AggregateMetricsRepository.get_latest.__annotations__
        assert "wallet_id" in get_latest_sig
        assert (
            get_latest_sig["wallet_id"] == str or get_latest_sig["wallet_id"] == "str"
        )
        assert (
            get_latest_sig["return"] == AggregateMetrics | None
            or get_latest_sig["return"] == "AggregateMetrics | None"
        )

        # Check get_history signature
        get_history_sig = AggregateMetricsRepository.get_history.__annotations__
        assert "wallet_id" in get_history_sig
        assert (
            get_history_sig["wallet_id"] == str or get_history_sig["wallet_id"] == "str"
        )
        assert "limit" in get_history_sig
        assert get_history_sig["limit"] == int or get_history_sig["limit"] == "int"
        assert "offset" in get_history_sig
        assert get_history_sig["offset"] == int or get_history_sig["offset"] == "int"
        ret = get_history_sig["return"]
        assert (
            ret == list[AggregateMetrics]
            or ret == "list[AggregateMetrics]"
            or ret == "List[AggregateMetrics]"
            or (
                isinstance(ret, str)
                and "AggregateMetrics" in ret
                and ("List" in ret or "list" in ret)
            )
        )
