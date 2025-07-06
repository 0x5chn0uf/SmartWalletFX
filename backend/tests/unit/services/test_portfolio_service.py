"""
Unit tests for PortfolioCalculationService.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest

from app.schemas.defi import PortfolioSnapshot as DefiPortfolioSnapshot


class TestPortfolioCalculationService:
    """Test cases for PortfolioCalculationService."""

    @pytest.mark.asyncio
    async def test_calculate_portfolio_metrics_with_snapshot(
        self, portfolio_service, mock_snapshot_data
    ):
        """Test calculating portfolio metrics with existing snapshot."""
        # Use a real PortfolioSnapshot Pydantic model for the mock snapshot
        from app.schemas.defi import (
            Borrowing,
            Collateral,
            HealthScore,
            PortfolioSnapshot,
            ProtocolName,
            StakedPosition,
        )

        snapshot = PortfolioSnapshot(
            user_address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            timestamp=int(datetime.utcnow().timestamp()),
            total_collateral=10.0,
            total_borrowings=2.0,
            total_collateral_usd=30000.0,
            total_borrowings_usd=2000.0,
            aggregate_health_score=0.85,
            aggregate_apy=0.08,
            collaterals=[
                Collateral(
                    protocol=ProtocolName.aave,
                    asset="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                    amount=1.5,
                    usd_value=4500.0,
                ),
                Collateral(
                    protocol=ProtocolName.compound,
                    asset="0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
                    amount=0.1,
                    usd_value=4500.0,
                ),
            ],
            borrowings=[
                Borrowing(
                    protocol=ProtocolName.aave,
                    asset="0xA0b86a33E6441b8C4C8C8C8C8C8C8C8C8C8C8C8",
                    amount=1000.0,
                    usd_value=1000.0,
                    interest_rate=0.05,
                ),
                Borrowing(
                    protocol=ProtocolName.compound,
                    asset="0x6B175474E89094C44Da98b954EedeAC495271d0F",
                    amount=500.0,
                    usd_value=500.0,
                    interest_rate=0.03,
                ),
            ],
            staked_positions=[
                StakedPosition(
                    protocol=ProtocolName.aave,
                    asset="0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
                    amount=10.0,
                    usd_value=1000.0,
                    apy=0.08,
                ),
            ],
            health_scores=[
                HealthScore(protocol=ProtocolName.aave, score=0.85, total_value=5500.0),
                HealthScore(
                    protocol=ProtocolName.compound, score=0.92, total_value=5000.0
                ),
            ],
            protocol_breakdown={},
        )
        portfolio_service._get_latest_snapshot = AsyncMock(return_value=snapshot)

        # Calculate metrics
        metrics = await portfolio_service.calculate_portfolio_metrics(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        )

        # Assertions
        assert metrics.user_address == "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        assert metrics.total_collateral == 1.6  # 1.5 + 0.1
        assert metrics.total_borrowings == 1500.0  # 1000 + 500
        assert metrics.total_collateral_usd == 9000.0  # 4500 + 4500
        assert metrics.total_borrowings_usd == 1500.0  # 1000 + 500
        assert metrics.aggregate_apy == 0.08  # Only one staked position
        assert len(metrics.collaterals) == 2
        assert len(metrics.borrowings) == 2
        assert len(metrics.staked_positions) == 1
        assert len(metrics.health_scores) == 2

    @pytest.mark.asyncio
    async def test_calculate_portfolio_metrics_debug(self, portfolio_service):
        """Debug test to understand why the service returns empty metrics."""
        # Create a simple mock snapshot
        mock_snapshot = Mock()
        mock_snapshot.collaterals = [Mock(amount=1.0, usd_value=100.0)]
        mock_snapshot.borrowings = [Mock(amount=0.5, usd_value=50.0)]
        mock_snapshot.staked_positions = [Mock(usd_value=10.0, apy=0.05)]
        mock_snapshot.health_scores = []

        portfolio_service._get_latest_snapshot = AsyncMock(return_value=mock_snapshot)

        # Try to calculate metrics and see what happens
        try:
            metrics = await portfolio_service.calculate_portfolio_metrics(
                "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
            )
            print(f"Metrics calculated successfully: {metrics}")

            # Debug: Check what the mock snapshot contains
            print(f"Mock snapshot collaterals: {mock_snapshot.collaterals}")
            print(f"Mock snapshot borrowings: {mock_snapshot.borrowings}")
            print(f"Mock snapshot staked_positions: {mock_snapshot.staked_positions}")

            # Debug: Check if the mock objects have the right attributes
            for i, collateral in enumerate(mock_snapshot.collaterals):
                print(
                    f"Collateral {i}: amount={getattr(collateral, 'amount', 'NOT_FOUND')}, usd_value={getattr(collateral, 'usd_value', 'NOT_FOUND')}"
                )

            for i, borrowing in enumerate(mock_snapshot.borrowings):
                print(
                    f"Borrowing {i}: amount={getattr(borrowing, 'amount', 'NOT_FOUND')}, usd_value={getattr(borrowing, 'usd_value', 'NOT_FOUND')}"
                )

        except Exception as e:
            print(f"Exception occurred: {e}")
            import traceback

            traceback.print_exc()

    @pytest.mark.asyncio
    async def test_calculate_portfolio_metrics_no_snapshot(self, portfolio_service):
        """Test calculating portfolio metrics with no snapshot."""
        portfolio_service._get_latest_snapshot = Mock(return_value=None)

        metrics = await portfolio_service.calculate_portfolio_metrics(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        )

        assert metrics.user_address == "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        assert metrics.total_collateral == 0.0
        assert metrics.total_borrowings == 0.0
        assert metrics.total_collateral_usd == 0.0
        assert metrics.total_borrowings_usd == 0.0
        assert metrics.aggregate_health_score is None
        assert metrics.aggregate_apy is None
        assert len(metrics.collaterals) == 0
        assert len(metrics.borrowings) == 0
        assert len(metrics.staked_positions) == 0
        assert len(metrics.health_scores) == 0

    @pytest.mark.asyncio
    async def test_calculate_portfolio_timeline(self, portfolio_service):
        """Test calculating portfolio timeline."""
        # Mock historical snapshots
        mock_snapshots = []
        for i in range(5):
            snapshot = Mock()
            snapshot.timestamp = int(
                (datetime.utcnow() - timedelta(days=i)).timestamp()
            )
            snapshot.total_collateral_usd = 10000.0 + (i * 100)
            snapshot.total_borrowings_usd = 2000.0 + (i * 50)
            mock_snapshots.append(snapshot)

        portfolio_service.snapshot_repo.get_snapshots_by_address_and_range = AsyncMock(
            return_value=mock_snapshots
        )

        timeline = await portfolio_service.calculate_portfolio_timeline(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e", limit=5
        )

        assert len(timeline.timestamps) == 5
        assert len(timeline.collateral_usd) == 5
        assert len(timeline.borrowings_usd) == 5
        # Most recent snapshot should be first (highest value)
        assert timeline.collateral_usd[0] == 10000.0
        assert timeline.borrowings_usd[0] == 2000.0

    def test_calculate_performance_metrics(self, portfolio_service):
        """Test calculating performance metrics."""
        # Mock snapshots for start and end dates
        start_snapshot_data = {
            "total_collateral_usd": 10000.0,
            "total_borrowings_usd": 2000.0,
        }
        end_snapshot_data = {
            "total_collateral_usd": 12000.0,
            "total_borrowings_usd": 2500.0,
        }

        # Mock the _get_snapshot_at_timestamp method
        portfolio_service._get_snapshot_at_timestamp = Mock()
        portfolio_service._get_snapshot_at_timestamp.side_effect = [
            DefiPortfolioSnapshot(**start_snapshot_data),
            DefiPortfolioSnapshot(**end_snapshot_data),
        ]

        # Mock max drawdown calculation
        portfolio_service._max_drawdown = Mock(return_value=0.15)

        result = portfolio_service.calculate_performance_metrics(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e", period_days=30
        )

        assert result["total_return"] == pytest.approx(
            0.1875, rel=1e-3
        )  # (9500 - 8000) / 8000
        assert result["max_drawdown"] == 0.15

    def test_calculate_performance_metrics_no_snapshots(self, portfolio_service):
        """Test calculating performance metrics with no snapshots."""
        portfolio_service._get_snapshot_at_timestamp = Mock(return_value=None)

        result = portfolio_service.calculate_performance_metrics(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e", period_days=30
        )

        assert result["total_return"] == 0.0
        assert result["max_drawdown"] == 0.0

    @pytest.mark.asyncio
    async def test_calculate_risk_metrics(self, portfolio_service):
        """Test calculating risk metrics."""
        # Mock snapshot with collaterals and borrowings
        mock_snapshot = Mock()
        mock_snapshot.collaterals = [
            Mock(usd_value=5000.0),
            Mock(usd_value=3000.0),
        ]
        mock_snapshot.borrowings = [
            Mock(usd_value=2000.0),
            Mock(usd_value=1000.0),
        ]

        portfolio_service._get_latest_snapshot = AsyncMock(return_value=mock_snapshot)

        result = await portfolio_service.calculate_risk_metrics(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        )

        assert result["collateralization_ratio"] == pytest.approx(
            2.67, rel=1e-2
        )  # 8000 / 3000
        assert result["utilization_rate"] == 0.375  # 3000 / 8000
        assert result["concentration_risk"] == 0.625  # 5000 / 8000

    @pytest.mark.asyncio
    async def test_calculate_risk_metrics_no_snapshot(self, portfolio_service):
        """Test calculating risk metrics with no snapshot."""
        portfolio_service._get_latest_snapshot = AsyncMock(return_value=None)

        result = await portfolio_service.calculate_risk_metrics(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        )

        assert result["collateralization_ratio"] == 0.0
        assert result["utilization_rate"] == 0.0
        assert result["concentration_risk"] == 0.0

    @pytest.mark.asyncio
    async def test_calculate_risk_metrics_zero_collateral(self, portfolio_service):
        """Test calculating risk metrics with zero collateral."""
        mock_snapshot = Mock()
        mock_snapshot.collaterals = []
        mock_snapshot.borrowings = [Mock(usd_value=1000.0)]

        portfolio_service._get_latest_snapshot = AsyncMock(return_value=mock_snapshot)

        result = await portfolio_service.calculate_risk_metrics(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        )

        assert result["collateralization_ratio"] == 0.0
        assert result["utilization_rate"] == 0.0
        assert result["concentration_risk"] == 0.0

    @pytest.mark.asyncio
    async def test_calculate_risk_metrics_zero_borrowings(self, portfolio_service):
        """Test calculating risk metrics with zero borrowings."""
        mock_snapshot = Mock()
        mock_snapshot.collaterals = [Mock(usd_value=5000.0)]
        mock_snapshot.borrowings = []

        portfolio_service._get_latest_snapshot = AsyncMock(return_value=mock_snapshot)

        result = await portfolio_service.calculate_risk_metrics(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        )

        assert result["collateralization_ratio"] == 0.0
        assert result["utilization_rate"] == 0.0
        assert result["concentration_risk"] == 1.0  # 5000 / 5000

    def test_calculate_aggregate_apy(self, portfolio_service):
        """Test calculating aggregate APY."""
        positions = [
            {"usd_value": 1000.0, "apy": 0.10},
            {"usd_value": 2000.0, "apy": 0.05},
            {"usd_value": 3000.0, "apy": 0.15},
        ]

        result = portfolio_service._aggregate_apy(positions)

        # Weighted average: (1000*0.10 + 2000*0.05 + 3000*0.15) / 6000 = 0.1083
        assert result == pytest.approx(0.1083, rel=1e-3)

    def test_calculate_aggregate_apy_empty(self, portfolio_service):
        """Test calculating aggregate APY with empty positions."""
        result = portfolio_service._aggregate_apy([])
        assert result is None

    def test_calculate_aggregate_apy_zero_total(self, portfolio_service):
        """Test calculating aggregate APY with zero total value."""
        positions = [
            {"usd_value": 0.0, "apy": 0.10},
            {"usd_value": 0.0, "apy": 0.05},
        ]

        result = portfolio_service._aggregate_apy(positions)
        assert result is None

    def test_calculate_total_return(self, portfolio_service):
        """Test calculating total return."""
        start_snapshot = DefiPortfolioSnapshot(
            total_collateral_usd=10000.0,
            total_borrowings_usd=2000.0,
        )
        end_snapshot = DefiPortfolioSnapshot(
            total_collateral_usd=12000.0,
            total_borrowings_usd=2500.0,
        )

        result = portfolio_service._total_return(start_snapshot, end_snapshot)

        # Net value: (12000-2500) - (10000-2000) = 9500 - 8000 = 1500
        # Return: 1500 / 8000 = 0.1875
        assert result == pytest.approx(0.1875, rel=1e-3)

    def test_calculate_total_return_zero_start(self, portfolio_service):
        """Test calculating total return with zero start value."""
        start_snapshot = DefiPortfolioSnapshot(
            total_collateral_usd=10000.0,
            total_borrowings_usd=10000.0,  # Net value = 0
        )
        end_snapshot = DefiPortfolioSnapshot(
            total_collateral_usd=12000.0,
            total_borrowings_usd=8000.0,
        )

        result = portfolio_service._total_return(start_snapshot, end_snapshot)
        assert result == 0.0

    def test_calculate_total_return_negative_start(self, portfolio_service):
        """Test calculating total return with negative start value."""
        start_snapshot = DefiPortfolioSnapshot(
            total_collateral_usd=10000.0,
            total_borrowings_usd=15000.0,  # Net value = -5000
        )
        end_snapshot = DefiPortfolioSnapshot(
            total_collateral_usd=12000.0,
            total_borrowings_usd=10000.0,  # Net value = 2000
        )

        result = portfolio_service._total_return(start_snapshot, end_snapshot)
        assert result == 0.0  # Should return 0 for negative start value

    def test_max_drawdown(self, portfolio_service):
        """Test calculating maximum drawdown."""
        # Mock _get_snapshot_at_timestamp to return snapshots with decreasing values
        portfolio_service._get_snapshot_at_timestamp = Mock()
        portfolio_service._get_snapshot_at_timestamp.side_effect = [
            DefiPortfolioSnapshot(
                total_collateral_usd=10000.0, total_borrowings_usd=2000.0
            ),  # Net: 8000
            DefiPortfolioSnapshot(
                total_collateral_usd=11000.0, total_borrowings_usd=2000.0
            ),  # Net: 9000 (peak)
            DefiPortfolioSnapshot(
                total_collateral_usd=9000.0, total_borrowings_usd=2000.0
            ),  # Net: 7000 (drawdown)
            DefiPortfolioSnapshot(
                total_collateral_usd=12000.0, total_borrowings_usd=2000.0
            ),  # Net: 10000 (new peak)
            DefiPortfolioSnapshot(
                total_collateral_usd=8000.0, total_borrowings_usd=2000.0
            ),  # Net: 6000 (drawdown)
        ]

        result = portfolio_service._max_drawdown(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            datetime.utcnow() - timedelta(days=4),
            datetime.utcnow(),
        )

        # Max drawdown should be (10000 - 6000) / 10000 = 0.4
        assert result == pytest.approx(0.4, rel=1e-3)

    def test_max_drawdown_no_snapshots(self, portfolio_service):
        """Test calculating maximum drawdown with no snapshots."""
        portfolio_service._get_snapshot_at_timestamp = Mock(return_value=None)

        result = portfolio_service._max_drawdown(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            datetime.utcnow() - timedelta(days=30),
            datetime.utcnow(),
        )

        assert result == 0.0

    def test_max_drawdown_increasing_values(self, portfolio_service):
        """Test calculating maximum drawdown with only increasing values."""
        portfolio_service._get_snapshot_at_timestamp = Mock()
        portfolio_service._get_snapshot_at_timestamp.side_effect = [
            DefiPortfolioSnapshot(
                total_collateral_usd=10000.0, total_borrowings_usd=2000.0
            ),
            DefiPortfolioSnapshot(
                total_collateral_usd=11000.0, total_borrowings_usd=2000.0
            ),
            DefiPortfolioSnapshot(
                total_collateral_usd=12000.0, total_borrowings_usd=2000.0
            ),
        ]

        result = portfolio_service._max_drawdown(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            datetime.utcnow() - timedelta(days=2),
            datetime.utcnow(),
        )

        assert result == 0.0  # No drawdown if values only increase

    @pytest.mark.asyncio
    async def test_error_handling_in_calculate_portfolio_metrics(
        self, portfolio_service
    ):
        """Test error handling in calculate_portfolio_metrics."""
        portfolio_service._get_latest_snapshot = Mock(
            side_effect=Exception("Database error")
        )

        metrics = await portfolio_service.calculate_portfolio_metrics(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        )

        # Should return empty metrics on error
        assert metrics.user_address == "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        assert metrics.total_collateral == 0.0
        assert metrics.total_borrowings == 0.0
        assert metrics.total_collateral_usd == 0.0
        assert metrics.total_borrowings_usd == 0.0

    @pytest.mark.asyncio
    async def test_error_handling_in_calculate_portfolio_timeline(
        self, portfolio_service
    ):
        """Test error handling in calculate_portfolio_timeline."""
        portfolio_service.snapshot_repo.get_snapshots_by_address_and_range = Mock(
            side_effect=Exception("Database error")
        )

        timeline = await portfolio_service.calculate_portfolio_timeline(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        )

        # Should return empty timeline on error
        assert timeline.timestamps == []
        assert timeline.collateral_usd == []
        assert timeline.borrowings_usd == []

    def test_calculate_aggregate_apy_with_dict_positions(self, portfolio_service):
        """Test calculating aggregate APY with dictionary positions."""
        positions = [
            {"usd_value": 1000.0, "apy": 0.10},
            {"usd_value": 2000.0, "apy": 0.05},
        ]

        result = portfolio_service._aggregate_apy(positions)
        assert result == pytest.approx(
            0.0667, rel=1e-3
        )  # (1000*0.10 + 2000*0.05) / 3000

    def test_calculate_aggregate_apy_with_object_positions(self, portfolio_service):
        """Test calculating aggregate APY with object positions."""

        class MockPosition:
            def __init__(self, usd_value, apy):
                self.usd_value = usd_value
                self.apy = apy

        positions = [
            MockPosition(1000.0, 0.10),
            MockPosition(2000.0, 0.05),
        ]

        result = portfolio_service._aggregate_apy(positions)
        assert result == pytest.approx(0.0667, rel=1e-3)

    def test_calculate_aggregate_apy_mixed_positions(self, portfolio_service):
        """Test calculating aggregate APY with mixed dict and object positions."""

        class MockPosition:
            def __init__(self, usd_value, apy):
                self.usd_value = usd_value
                self.apy = apy

        positions = [
            {"usd_value": 1000.0, "apy": 0.10},
            MockPosition(2000.0, 0.05),
            {"usd_value": 3000.0, "apy": 0.15},
        ]

        result = portfolio_service._aggregate_apy(positions)
        assert result == pytest.approx(0.1083, rel=1e-3)

    def test_calculate_aggregate_apy_missing_attributes(self, portfolio_service):
        """Test calculating aggregate APY with missing attributes."""
        positions = [
            {"usd_value": 1000.0, "apy": 0.10},
            {"usd_value": 2000.0},  # Missing apy
            {"apy": 0.15},  # Missing usd_value
        ]

        result = portfolio_service._aggregate_apy(positions)
        # Should use default values (0.0) for missing attributes
        assert result == pytest.approx(
            0.0333, rel=1e-3
        )  # (1000*0.10 + 2000*0.0 + 0*0.15) / 3000

    @pytest.mark.asyncio
    async def test_get_latest_snapshot(self, portfolio_service):
        """Test getting latest snapshot."""
        mock_snapshot = Mock()
        portfolio_service.snapshot_repo.get_latest_snapshot_by_address = AsyncMock(
            return_value=mock_snapshot
        )

        result = await portfolio_service._get_latest_snapshot("0x123...")

        assert result == mock_snapshot
        portfolio_service.snapshot_repo.get_latest_snapshot_by_address.assert_called_once_with(
            "0x123..."
        )

    def test_empty_metrics(self, portfolio_service):
        """Test creating empty metrics."""
        result = portfolio_service._empty_metrics("0x123...")

        assert result.user_address == "0x123..."
        assert result.total_collateral == 0.0
        assert result.total_borrowings == 0.0
        assert result.total_collateral_usd == 0.0
        assert result.total_borrowings_usd == 0.0
        assert result.aggregate_health_score is None
        assert result.aggregate_apy is None
        assert len(result.collaterals) == 0
        assert len(result.borrowings) == 0
        assert len(result.staked_positions) == 0
        assert len(result.health_scores) == 0

    def test_empty_performance(self, portfolio_service):
        """Test creating empty performance metrics."""
        result = portfolio_service._empty_performance()

        assert result["total_return"] == 0.0
        assert result["max_drawdown"] == 0.0

    def test_calculate_aggregate_apy_static_method(self, portfolio_service):
        """Test the static _calculate_aggregate_apy method."""
        positions = [
            {"usd_value": 1000.0, "apy": 0.10},
            {"usd_value": 2000.0, "apy": 0.05},
        ]

        result = portfolio_service._calculate_aggregate_apy(positions)
        assert result == pytest.approx(0.0667, rel=1e-3)

    def test_calculate_total_return_static_method(self, portfolio_service):
        """Test the static _calculate_total_return method."""
        start_snapshot = DefiPortfolioSnapshot(
            total_collateral_usd=10000.0,
            total_borrowings_usd=2000.0,
        )
        end_snapshot = DefiPortfolioSnapshot(
            total_collateral_usd=12000.0,
            total_borrowings_usd=2500.0,
        )

        result = portfolio_service._calculate_total_return(start_snapshot, end_snapshot)
        assert result == pytest.approx(0.1875, rel=1e-3)
