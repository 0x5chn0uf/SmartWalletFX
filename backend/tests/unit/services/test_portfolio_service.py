"""
Unit tests for PortfolioCalculationService.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

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

    def test_calculate_portfolio_metrics_with_snapshot(
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
        metrics = portfolio_service.calculate_portfolio_metrics(
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

    def test_calculate_portfolio_metrics_no_snapshot(self, portfolio_service):
        """Test calculating portfolio metrics when no snapshot exists."""
        portfolio_service._get_latest_snapshot = Mock(return_value=None)

        metrics = portfolio_service.calculate_portfolio_metrics(
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

    def test_calculate_portfolio_timeline(self, portfolio_service):
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

        portfolio_service._get_historical_snapshots = Mock(return_value=mock_snapshots)

        timeline = portfolio_service.calculate_portfolio_timeline(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e", limit=5
        )

        assert len(timeline.timestamps) == 5
        assert len(timeline.collateral_usd) == 5
        assert len(timeline.borrowings_usd) == 5
        assert timeline.collateral_usd[0] == 10400.0  # Most recent
        assert timeline.borrowings_usd[0] == 2200.0  # Most recent

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

        portfolio_service._get_snapshot_at_timestamp = Mock(
            side_effect=[
                DefiPortfolioSnapshot(**start_snapshot_data),
                DefiPortfolioSnapshot(**end_snapshot_data),
            ]
        )

        # Mock volatility calculation
        portfolio_service._calculate_volatility = Mock(return_value=0.1)

        metrics = portfolio_service.calculate_performance_metrics(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e", period_days=30
        )

        assert metrics["total_return"] == pytest.approx(
            0.1875, rel=1e-3
        )  # (9500-8000)/8000
        assert metrics["volatility"] == 0.1
        assert metrics["sharpe_ratio"] == pytest.approx(1.875, rel=1e-3)  # 0.1875/0.1
        assert metrics["period_days"] == 30

    def test_calculate_risk_metrics(self, portfolio_service):
        """Test calculating risk metrics."""
        # Mock portfolio metrics
        mock_metrics = Mock()
        mock_metrics.total_collateral_usd = 10000.0
        mock_metrics.total_borrowings_usd = 2000.0
        mock_metrics.aggregate_health_score = 0.85
        mock_metrics.collaterals = [Mock(usd_value=6000.0), Mock(usd_value=4000.0)]

        portfolio_service.calculate_portfolio_metrics = Mock(return_value=mock_metrics)

        # Mock helper methods
        portfolio_service._calculate_diversification_score = Mock(return_value=0.8)
        portfolio_service._calculate_concentration_risk = Mock(return_value=0.6)

        risk_metrics = portfolio_service.calculate_risk_metrics(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        )

        assert risk_metrics["collateralization_ratio"] == 5.0  # 10000/2000
        assert risk_metrics["utilization_rate"] == 0.2  # 2000/10000
        assert risk_metrics["diversification_score"] == 0.8
        assert risk_metrics["concentration_risk"] == 0.6
        assert risk_metrics["aggregate_health_score"] == 0.85

    def test_calculate_aggregate_health_score(self, portfolio_service):
        """Test calculating aggregate health score."""
        health_scores = [
            {"score": 0.8, "total_value": 1000.0},
            {"score": 0.9, "total_value": 2000.0},
        ]

        aggregate_score = portfolio_service._calculate_aggregate_health_score(
            health_scores
        )

        # Weighted average: (0.8*1000 + 0.9*2000) / (1000 + 2000) = 0.867
        assert aggregate_score == pytest.approx(0.867, rel=1e-3)

    def test_calculate_aggregate_health_score_empty(self, portfolio_service):
        """Test calculating aggregate health score with empty data."""
        aggregate_score = portfolio_service._calculate_aggregate_health_score([])

        assert aggregate_score is None

    def test_calculate_aggregate_apy(self, portfolio_service):
        """Test calculating aggregate APY."""
        staked_positions = [
            {"usd_value": 1000.0, "apy": 0.08},
            {"usd_value": 2000.0, "apy": 0.12},
        ]

        aggregate_apy = portfolio_service._calculate_aggregate_apy(staked_positions)

        # Weighted average: (0.08*1000 + 0.12*2000) / (1000 + 2000) = 0.107
        assert aggregate_apy == pytest.approx(0.107, rel=1e-3)

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

    def test_calculate_sharpe_ratio(self, portfolio_service):
        """Test calculating Sharpe ratio."""
        sharpe_ratio = portfolio_service._calculate_sharpe_ratio(0.1, 0.05)

        assert sharpe_ratio == 2.0  # 0.1/0.05

    def test_calculate_sharpe_ratio_zero_volatility(self, portfolio_service):
        """Test calculating Sharpe ratio with zero volatility."""
        sharpe_ratio = portfolio_service._calculate_sharpe_ratio(0.1, 0.0)

        assert sharpe_ratio == 0.0

    def test_calculate_diversification_score(self, portfolio_service):
        """Test calculating diversification score."""
        mock_metrics = Mock()
        mock_metrics.collaterals = [Mock(usd_value=5000.0), Mock(usd_value=5000.0)]

        diversification_score = portfolio_service._calculate_diversification_score(
            mock_metrics
        )

        # Perfect diversification (50/50 split) should give score close to 1
        assert diversification_score == pytest.approx(1.0, rel=1e-3)

    def test_calculate_diversification_score_concentrated(self, portfolio_service):
        """Test calculating diversification score for concentrated portfolio."""
        mock_metrics = Mock()
        mock_metrics.collaterals = [Mock(usd_value=9000.0), Mock(usd_value=1000.0)]

        diversification_score = portfolio_service._calculate_diversification_score(
            mock_metrics
        )

        # Highly concentrated portfolio should give low score
        assert diversification_score < 0.5

    def test_calculate_concentration_risk(self, portfolio_service):
        """Test calculating concentration risk."""
        mock_metrics = Mock()
        mock_metrics.collaterals = [Mock(usd_value=8000.0), Mock(usd_value=2000.0)]

        concentration_risk = portfolio_service._calculate_concentration_risk(
            mock_metrics
        )

        # Largest position is 80% of total
        assert concentration_risk == 0.8

    def test_calculate_max_drawdown(self, portfolio_service):
        """Test calculating maximum drawdown."""
        # Mock historical snapshots
        portfolio_service._get_snapshot_at_timestamp = Mock(
            side_effect=[
                DefiPortfolioSnapshot(
                    total_collateral_usd=10000.0, total_borrowings_usd=2000.0
                ),
                DefiPortfolioSnapshot(
                    total_collateral_usd=12000.0, total_borrowings_usd=2000.0
                ),
                DefiPortfolioSnapshot(
                    total_collateral_usd=8000.0, total_borrowings_usd=2000.0
                ),
                DefiPortfolioSnapshot(
                    total_collateral_usd=11000.0, total_borrowings_usd=2000.0
                ),
            ]
        )

        max_drawdown = portfolio_service._calculate_max_drawdown(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            datetime.utcnow() - timedelta(days=3),
            datetime.utcnow(),
        )

        # Peak: 10000, Trough: 6000, Drawdown: (10000-6000)/10000 = 0.4
        assert max_drawdown == pytest.approx(0.4, rel=1e-3)

    def test_create_protocol_breakdown(self, portfolio_service, mock_snapshot_data):
        """Test creating protocol breakdown."""
        snapshot = DefiPortfolioSnapshot(**mock_snapshot_data)

        breakdown = portfolio_service._create_protocol_breakdown(
            [c for c in snapshot.collaterals],
            [b for b in snapshot.borrowings],
            [p for p in snapshot.staked_positions],
            [h for h in snapshot.health_scores],
        )

        assert "AAVE" in breakdown
        assert "COMPOUND" in breakdown
        assert breakdown["AAVE"]["total_collateral"] == 1.5
        assert breakdown["AAVE"]["total_borrowings"] == 1000.0
        assert breakdown["COMPOUND"]["total_collateral"] == 0.1
        assert breakdown["COMPOUND"]["total_borrowings"] == 500.0

    def test_error_handling_in_calculate_portfolio_metrics(self, portfolio_service):
        """Test error handling in calculate_portfolio_metrics."""
        portfolio_service._get_latest_snapshot = Mock(
            side_effect=Exception("Database error")
        )

        metrics = portfolio_service.calculate_portfolio_metrics(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        )

        # Should return empty metrics on error
        assert metrics.user_address == "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        assert metrics.total_collateral == 0.0
        assert metrics.total_borrowings == 0.0

    def test_error_handling_in_calculate_portfolio_timeline(self, portfolio_service):
        """Test error handling in calculate_portfolio_timeline."""
        portfolio_service._get_historical_snapshots = Mock(
            side_effect=Exception("Database error")
        )

        timeline = portfolio_service.calculate_portfolio_timeline(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        )

        # Should return empty timeline on error
        assert len(timeline.timestamps) == 0
        assert len(timeline.collateral_usd) == 0
        assert len(timeline.borrowings_usd) == 0
