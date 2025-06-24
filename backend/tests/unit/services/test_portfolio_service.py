"""
Unit tests for PortfolioCalculationService.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.models.portfolio_snapshot import PortfolioSnapshot
from app.schemas.defi import PortfolioSnapshot as DefiPortfolioSnapshot
from app.schemas.portfolio_metrics import PortfolioMetrics
from app.schemas.portfolio_timeline import PortfolioTimeline
from app.services.portfolio_service import PortfolioCalculationService


class TestPortfolioCalculationService:
    """Test cases for PortfolioCalculationService."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def portfolio_service(self, mock_db_session):
        """Portfolio calculation service instance."""
        return PortfolioCalculationService(mock_db_session)

    @pytest.fixture
    def mock_snapshot_data(self):
        """Mock portfolio snapshot data."""
        return {
            "user_address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            "timestamp": int(datetime.utcnow().timestamp()),
            "total_collateral": 10.0,
            "total_borrowings": 2.0,
            "total_collateral_usd": 30000.0,
            "total_borrowings_usd": 2000.0,
            "aggregate_health_score": 0.85,
            "aggregate_apy": 0.08,
            "collaterals": [
                {
                    "protocol": "AAVE",
                    "asset": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                    "amount": 1.5,
                    "usd_value": 4500.0,
                },
                {
                    "protocol": "COMPOUND",
                    "asset": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
                    "amount": 0.1,
                    "usd_value": 4500.0,
                },
            ],
            "borrowings": [
                {
                    "protocol": "AAVE",
                    "asset": "0xA0b86a33E6441b8C4C8C8C8C8C8C8C8C8C8C8C8",
                    "amount": 1000.0,
                    "usd_value": 1000.0,
                    "interest_rate": 0.05,
                },
                {
                    "protocol": "COMPOUND",
                    "asset": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
                    "amount": 500.0,
                    "usd_value": 500.0,
                    "interest_rate": 0.03,
                },
            ],
            "staked_positions": [
                {
                    "protocol": "AAVE",
                    "asset": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
                    "amount": 10.0,
                    "usd_value": 1000.0,
                    "apy": 0.08,
                }
            ],
            "health_scores": [
                {"protocol": "AAVE", "score": 0.85, "total_value": 5500.0},
                {"protocol": "COMPOUND", "score": 0.92, "total_value": 5000.0},
            ],
            "protocol_breakdown": {
                "AAVE": {
                    "protocol": "AAVE",
                    "total_collateral": 1.5,
                    "total_borrowings": 1000.0,
                    "aggregate_health_score": 0.85,
                    "aggregate_apy": 0.08,
                },
                "COMPOUND": {
                    "protocol": "COMPOUND",
                    "total_collateral": 0.1,
                    "total_borrowings": 500.0,
                    "aggregate_health_score": 0.92,
                    "aggregate_apy": 0.0,
                },
            },
        }

    async def test_calculate_portfolio_metrics_with_snapshot(
        self, portfolio_service, mock_snapshot_data
    ):
        """Test calculating portfolio metrics with existing snapshot."""
        # Mock database query
        mock_snapshot = Mock()
        for key, value in mock_snapshot_data.items():
            setattr(mock_snapshot, key, value)

        portfolio_service._get_latest_snapshot = Mock(
            return_value=DefiPortfolioSnapshot(**mock_snapshot_data)
        )

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
        assert metrics.aggregate_health_score == pytest.approx(
            0.884, rel=1e-3
        )  # Weighted average
        assert metrics.aggregate_apy == 0.08  # Only one staked position
        assert len(metrics.collaterals) == 2
        assert len(metrics.borrowings) == 2
        assert len(metrics.staked_positions) == 1
        assert len(metrics.health_scores) == 2

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

        portfolio_service.snapshot_repo.get_snapshots_by_address_and_range = Mock(
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

        # 31 snapshots for volatility, 31 for max_drawdown
        volatility_snapshots = [
            DefiPortfolioSnapshot(
                total_collateral_usd=10000.0 + (i * 10),
                total_borrowings_usd=2000.0 + (i * 5),
            )
            for i in range(31)
        ]
        max_drawdown_snapshots = [
            DefiPortfolioSnapshot(
                total_collateral_usd=10000.0 + (i * 10),
                total_borrowings_usd=2000.0 + (i * 5),
            )
            for i in range(31)
        ]

        portfolio_service._get_snapshot_at_timestamp = Mock(
            side_effect=[
                DefiPortfolioSnapshot(**start_snapshot_data),  # For start date
                DefiPortfolioSnapshot(**end_snapshot_data),  # For end date
                *volatility_snapshots,  # For volatility (31)
                *max_drawdown_snapshots,  # For max_drawdown (31)
            ]
        )

        metrics = portfolio_service.calculate_performance_metrics(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e", period_days=30
        )

        assert metrics["total_return"] == pytest.approx(0.1875, rel=1e-3)
        assert metrics["max_drawdown"] >= 0.0

    @pytest.mark.asyncio
    async def test_calculate_risk_metrics(self, portfolio_service):
        """Test calculating risk metrics."""
        # Mock snapshot with the correct structure
        mock_snapshot = Mock()
        mock_snapshot.collaterals = [Mock(usd_value=6000.0), Mock(usd_value=4000.0)]
        mock_snapshot.borrowings = [Mock(usd_value=2000.0)]
        mock_snapshot.health_scores = [Mock(score=0.85, total_value=10000.0)]

        portfolio_service._get_latest_snapshot = AsyncMock(return_value=mock_snapshot)

        risk_metrics = await portfolio_service.calculate_risk_metrics(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        )

        assert risk_metrics["collateralization_ratio"] == 5.0  # 10000/2000
        assert risk_metrics["utilization_rate"] == 0.2  # 2000/10000
        assert risk_metrics["concentration_risk"] == 0.6  # 6000/10000

    def test_calculate_aggregate_apy(self, portfolio_service):
        """Test calculating aggregate APY."""
        staked_positions = [
            {"usd_value": 1000.0, "apy": 0.08},
            {"usd_value": 2000.0, "apy": 0.12},
        ]

        aggregate_apy = portfolio_service._calculate_aggregate_apy(staked_positions)

        # Weighted average: (0.08*1000 + 0.12*2000) / (1000 + 2000) = 0.1067
        assert aggregate_apy == pytest.approx(0.1067, rel=1e-3)

    def test_calculate_aggregate_apy_empty(self, portfolio_service):
        """Test calculating aggregate APY with empty data."""
        aggregate_apy = portfolio_service._calculate_aggregate_apy([])

        assert aggregate_apy is None

    def test_calculate_total_return(self, portfolio_service):
        """Test calculating total return."""
        start_snapshot = DefiPortfolioSnapshot(
            total_collateral_usd=10000.0, total_borrowings_usd=2000.0
        )
        end_snapshot = DefiPortfolioSnapshot(
            total_collateral_usd=12000.0, total_borrowings_usd=2500.0
        )

        total_return = portfolio_service._calculate_total_return(
            start_snapshot, end_snapshot
        )

        # Net value: start=8000, end=9500, return=(9500-8000)/8000 = 0.1875
        assert total_return == pytest.approx(0.1875, rel=1e-3)

    def test_calculate_total_return_zero_start(self, portfolio_service):
        """Test calculating total return with zero start value."""
        start_snapshot = DefiPortfolioSnapshot(
            total_collateral_usd=2000.0, total_borrowings_usd=2000.0
        )
        end_snapshot = DefiPortfolioSnapshot(
            total_collateral_usd=3000.0, total_borrowings_usd=1000.0
        )

        total_return = portfolio_service._calculate_total_return(
            start_snapshot, end_snapshot
        )

        assert total_return == 0.0

    @pytest.mark.asyncio
    async def test_error_handling_in_calculate_portfolio_metrics(
        self, portfolio_service
    ):
        """Test error handling in calculate_portfolio_metrics."""
        # Simulate error by patching _get_latest_snapshot to raise
        portfolio_service._get_latest_snapshot = AsyncMock(
            side_effect=Exception("DB error")
        )

        metrics = await portfolio_service.calculate_portfolio_metrics(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        )

        assert metrics.user_address == "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        assert metrics.aggregate_health_score is None
        assert metrics.aggregate_apy is None
        assert metrics.collaterals == []
        assert metrics.borrowings == []
        assert metrics.staked_positions == []

    @pytest.mark.asyncio
    async def test_error_handling_in_calculate_portfolio_timeline(
        self, portfolio_service
    ):
        """Test error handling in calculate_portfolio_timeline."""
        portfolio_service.snapshot_repo.get_snapshots_by_address_and_range = AsyncMock(
            side_effect=Exception("Database error")
        )

        timeline = await portfolio_service.calculate_portfolio_timeline(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        )

        # Should return empty timeline on error
        assert len(timeline.timestamps) == 0
        assert len(timeline.collateral_usd) == 0
        assert len(timeline.borrowings_usd) == 0
