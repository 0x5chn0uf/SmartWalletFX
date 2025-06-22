"""
Unit tests for DataAnalysisService.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.schemas.portfolio_metrics import PortfolioMetrics
from app.schemas.portfolio_timeline import PortfolioTimeline
from app.services.blockchain_service import BlockchainService
from app.services.data_analysis_service import DataAnalysisService
from app.services.portfolio_service import PortfolioCalculationService


class TestDataAnalysisService:
    """Test cases for DataAnalysisService."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def data_analysis_service(self, mock_db_session):
        """Data analysis service instance."""
        return DataAnalysisService(mock_db_session)

    @pytest.fixture
    def mock_portfolio_metrics(self):
        """Mock portfolio metrics."""
        return Mock(
            user_address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            total_collateral=10.0,
            total_borrowings=2.0,
            total_collateral_usd=30000.0,
            total_borrowings_usd=2000.0,
            aggregate_health_score=0.85,
            aggregate_apy=0.08,
            collaterals=[Mock(usd_value=15000.0), Mock(usd_value=15000.0)],
        )

    @pytest.mark.asyncio
    async def test_analyze_portfolio_comprehensive_success(
        self, data_analysis_service, mock_portfolio_metrics
    ):
        """Test comprehensive portfolio analysis success."""
        # Mock portfolio service methods
        with patch.object(
            data_analysis_service.portfolio_service,
            "calculate_portfolio_metrics",
            return_value=mock_portfolio_metrics,
        ), patch.object(
            data_analysis_service.portfolio_service,
            "calculate_risk_metrics",
            return_value={
                "collateralization_ratio": 15.0,
                "utilization_rate": 0.067,
                "diversification_score": 0.8,
                "concentration_risk": 0.5,
                "aggregate_health_score": 0.85,
            },
        ), patch.object(
            data_analysis_service.portfolio_service,
            "calculate_performance_metrics",
            return_value={
                "total_return": 0.15,
                "volatility": 0.1,
                "sharpe_ratio": 1.5,
                "max_drawdown": 0.05,
                "period_days": 30,
            },
        ), patch.object(
            data_analysis_service,
            "_get_real_time_data",
            return_value={
                "balances": {"0x123": {"balance": "1000000000000000000"}},
                "defi_positions": {"collaterals": [], "borrowings": []},
                "portfolio_value": {"total_value": 28000.0},
            },
        ), patch.object(
            data_analysis_service,
            "_get_historical_analysis",
            return_value={
                "timeline": PortfolioTimeline(
                    timestamps=[], collateral_usd=[], borrowings_usd=[]
                ),
                "historical_data": [],
                "analysis_period": "90_days",
                "data_points": 0,
            },
        ):
            analysis = await data_analysis_service.analyze_portfolio_comprehensive(
                "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
            )

            assert (
                analysis["user_address"] == "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
            )
            assert analysis["portfolio_metrics"] == mock_portfolio_metrics
            assert analysis["real_time_data"] is not None
            assert analysis["historical_analysis"] is not None
            assert analysis["risk_assessment"] is not None
            assert analysis["performance_metrics"] is not None
            assert analysis["predictions"] is None  # Not enabled by default

    @pytest.mark.asyncio
    async def test_analyze_portfolio_comprehensive_with_predictions(
        self, data_analysis_service, mock_portfolio_metrics
    ):
        """Test comprehensive portfolio analysis with predictions enabled."""
        # Mock all methods
        with patch.object(
            data_analysis_service.portfolio_service,
            "calculate_portfolio_metrics",
            return_value=mock_portfolio_metrics,
        ), patch.object(
            data_analysis_service.portfolio_service,
            "calculate_risk_metrics",
            return_value={},
        ), patch.object(
            data_analysis_service.portfolio_service,
            "calculate_performance_metrics",
            return_value={},
        ), patch.object(
            data_analysis_service, "_get_real_time_data", return_value={}
        ), patch.object(
            data_analysis_service, "_get_historical_analysis", return_value={}
        ), patch.object(
            data_analysis_service,
            "_generate_predictions",
            return_value={
                "predictions": [
                    {"day": 1, "predicted_value": 29000.0, "confidence": 0.9}
                ],
                "trend": 0.05,
                "confidence": 0.7,
            },
        ):
            analysis = await data_analysis_service.analyze_portfolio_comprehensive(
                "0x742d35Cc6634C0532925a3b844Bc454e4438f44e", include_predictions=True
            )

            assert analysis["predictions"] is not None
            assert len(analysis["predictions"]["predictions"]) > 0

    @pytest.mark.asyncio
    async def test_analyze_portfolio_comprehensive_error_handling(
        self, data_analysis_service
    ):
        """Test comprehensive portfolio analysis error handling."""
        # Mock portfolio service to raise exception
        with patch.object(
            data_analysis_service.portfolio_service,
            "calculate_portfolio_metrics",
            side_effect=Exception("Database error"),
        ):
            analysis = await data_analysis_service.analyze_portfolio_comprehensive(
                "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
            )

            assert analysis["error"] == "Analysis failed"
            assert analysis["portfolio_metrics"] is None

    @pytest.mark.asyncio
    async def test_analyze_market_trends(self, data_analysis_service):
        """Test market trends analysis."""
        tokens = [
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        ]

        # Mock historical data
        mock_historical_data = [
            {"timestamp": 1234567890, "price": 100.0, "volume": 1000000},
            {"timestamp": 1234567890 + 86400, "price": 110.0, "volume": 1100000},
            {"timestamp": 1234567890 + 172800, "price": 105.0, "volume": 1050000},
        ]

        with patch.object(
            data_analysis_service,
            "_get_token_historical_data",
            return_value=mock_historical_data,
        ):
            trends = await data_analysis_service.analyze_market_trends(
                tokens, period_days=30
            )

            assert trends["analysis_period"] == 30
            assert trends["tokens_analyzed"] == 2
            assert len(trends["trends"]) == 2
            assert "market_sentiment" in trends

    @pytest.mark.asyncio
    async def test_analyze_market_trends_error_handling(self, data_analysis_service):
        """Test market trends analysis error handling."""
        with patch.object(
            data_analysis_service,
            "_get_token_historical_data",
            side_effect=Exception("API error"),
        ):
            trends = await data_analysis_service.analyze_market_trends(
                ["0x123"], period_days=30
            )

            assert trends["trends"] == {}
            assert trends["market_sentiment"] == "neutral"

    @pytest.mark.asyncio
    async def test_generate_portfolio_insights_low_diversification(
        self, data_analysis_service, mock_portfolio_metrics
    ):
        """Test generating portfolio insights for low diversification."""
        # Mock metrics with low diversification
        with patch.object(
            data_analysis_service.portfolio_service,
            "calculate_portfolio_metrics",
            return_value=mock_portfolio_metrics,
        ), patch.object(
            data_analysis_service.portfolio_service,
            "calculate_risk_metrics",
            return_value={
                "diversification_score": 0.3,  # Low diversification
                "utilization_rate": 0.5,
                "aggregate_health_score": 0.85,
            },
        ), patch.object(
            data_analysis_service.portfolio_service,
            "calculate_performance_metrics",
            return_value={"total_return": 0.1},
        ):
            insights = await data_analysis_service.generate_portfolio_insights(
                "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
            )

            # Should have diversification insight
            diversification_insights = [
                i for i in insights if i["type"] == "diversification"
            ]
            assert len(diversification_insights) > 0
            assert diversification_insights[0]["severity"] == "medium"

    @pytest.mark.asyncio
    async def test_generate_portfolio_insights_low_health_score(
        self, data_analysis_service
    ):
        """Test generating portfolio insights for low health score."""
        mock_metrics = Mock(
            aggregate_health_score=0.6,  # Low health score
            aggregate_apy=0.08,
            collaterals=[Mock(usd_value=10000.0)],
        )

        with patch.object(
            data_analysis_service.portfolio_service,
            "calculate_portfolio_metrics",
            return_value=mock_metrics,
        ), patch.object(
            data_analysis_service.portfolio_service,
            "calculate_risk_metrics",
            return_value={
                "diversification_score": 0.8,
                "utilization_rate": 0.5,
                "aggregate_health_score": 0.6,
            },
        ), patch.object(
            data_analysis_service.portfolio_service,
            "calculate_performance_metrics",
            return_value={"total_return": 0.1},
        ):
            insights = await data_analysis_service.generate_portfolio_insights(
                "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
            )

            # Should have health score insight
            health_insights = [i for i in insights if i["type"] == "health_score"]
            assert len(health_insights) > 0
            assert health_insights[0]["severity"] == "high"

    @pytest.mark.asyncio
    async def test_generate_portfolio_insights_negative_performance(
        self, data_analysis_service
    ):
        """Test generating portfolio insights for negative performance."""
        mock_metrics = Mock(
            aggregate_health_score=0.85,
            aggregate_apy=0.08,
            collaterals=[Mock(usd_value=10000.0)],
        )

        with patch.object(
            data_analysis_service.portfolio_service,
            "calculate_portfolio_metrics",
            return_value=mock_metrics,
        ), patch.object(
            data_analysis_service.portfolio_service,
            "calculate_risk_metrics",
            return_value={
                "diversification_score": 0.8,
                "utilization_rate": 0.5,
                "aggregate_health_score": 0.85,
            },
        ), patch.object(
            data_analysis_service.portfolio_service,
            "calculate_performance_metrics",
            return_value={"total_return": -0.1},  # Negative performance
        ):
            insights = await data_analysis_service.generate_portfolio_insights(
                "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
            )

            # Should have performance insight
            performance_insights = [i for i in insights if i["type"] == "performance"]
            assert len(performance_insights) > 0
            assert performance_insights[0]["severity"] == "medium"

    @pytest.mark.asyncio
    async def test_generate_portfolio_insights_high_utilization(
        self, data_analysis_service
    ):
        """Test generating portfolio insights for high utilization."""
        mock_metrics = Mock(
            aggregate_health_score=0.85,
            aggregate_apy=0.08,
            collaterals=[Mock(usd_value=10000.0)],
        )

        with patch.object(
            data_analysis_service.portfolio_service,
            "calculate_portfolio_metrics",
            return_value=mock_metrics,
        ), patch.object(
            data_analysis_service.portfolio_service,
            "calculate_risk_metrics",
            return_value={
                "diversification_score": 0.8,
                "utilization_rate": 0.85,  # High utilization
                "aggregate_health_score": 0.85,
            },
        ), patch.object(
            data_analysis_service.portfolio_service,
            "calculate_performance_metrics",
            return_value={"total_return": 0.1},
        ):
            insights = await data_analysis_service.generate_portfolio_insights(
                "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
            )

            # Should have utilization insight
            utilization_insights = [i for i in insights if i["type"] == "utilization"]
            assert len(utilization_insights) > 0
            assert utilization_insights[0]["severity"] == "high"

    @pytest.mark.asyncio
    async def test_generate_portfolio_insights_low_yield(self, data_analysis_service):
        """Test generating portfolio insights for low yield."""
        mock_metrics = Mock(
            aggregate_health_score=0.85,
            aggregate_apy=0.03,  # Low APY
            collaterals=[Mock(usd_value=10000.0)],
        )

        with patch.object(
            data_analysis_service.portfolio_service,
            "calculate_portfolio_metrics",
            return_value=mock_metrics,
        ), patch.object(
            data_analysis_service.portfolio_service,
            "calculate_risk_metrics",
            return_value={
                "diversification_score": 0.8,
                "utilization_rate": 0.5,
                "aggregate_health_score": 0.85,
            },
        ), patch.object(
            data_analysis_service.portfolio_service,
            "calculate_performance_metrics",
            return_value={"total_return": 0.1},
        ):
            insights = await data_analysis_service.generate_portfolio_insights(
                "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
            )

            # Should have yield insight
            yield_insights = [i for i in insights if i["type"] == "yield"]
            assert len(yield_insights) > 0
            assert yield_insights[0]["severity"] == "low"

    @pytest.mark.asyncio
    async def test_calculate_portfolio_efficiency(
        self, data_analysis_service, mock_portfolio_metrics
    ):
        """Test calculating portfolio efficiency."""
        with patch.object(
            data_analysis_service.portfolio_service,
            "calculate_portfolio_metrics",
            return_value=mock_portfolio_metrics,
        ), patch.object(
            data_analysis_service.portfolio_service,
            "calculate_performance_metrics",
            return_value={"sharpe_ratio": 1.5},
        ), patch.object(
            data_analysis_service.portfolio_service,
            "calculate_risk_metrics",
            return_value={"diversification_score": 0.8, "aggregate_health_score": 0.85},
        ):
            efficiency = await data_analysis_service.calculate_portfolio_efficiency(
                "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
            )

            assert "efficiency_score" in efficiency
            assert "sharpe_ratio" in efficiency
            assert "diversification_score" in efficiency
            assert "health_score" in efficiency
            assert "risk_adjusted_return" in efficiency
            assert "portfolio_quality" in efficiency

            # Efficiency score should be between 0 and 100
            assert 0 <= efficiency["efficiency_score"] <= 100

    @pytest.mark.asyncio
    async def test_calculate_portfolio_efficiency_error_handling(
        self, data_analysis_service
    ):
        """Test portfolio efficiency calculation error handling."""
        with patch.object(
            data_analysis_service.portfolio_service,
            "calculate_portfolio_metrics",
            side_effect=Exception("Error"),
        ):
            efficiency = await data_analysis_service.calculate_portfolio_efficiency(
                "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
            )

            assert efficiency["efficiency_score"] == 0.0
            assert efficiency["sharpe_ratio"] == 0.0
            assert efficiency["diversification_score"] == 0.0
            assert efficiency["health_score"] == 0.0

    @pytest.mark.asyncio
    async def test_get_real_time_data(self, data_analysis_service):
        """Test getting real-time data."""
        with patch.object(
            data_analysis_service.blockchain_service,
            "get_wallet_balances",
            return_value={"0x123": {"balance": "1000000000000000000"}},
        ), patch.object(
            data_analysis_service.blockchain_service,
            "get_defi_positions",
            return_value={
                "collaterals": [],
                "borrowings": [],
                "staked_positions": [],
                "health_scores": [],
            },
        ), patch.object(
            data_analysis_service.blockchain_service,
            "calculate_portfolio_value",
            return_value={"total_value": 28000.0, "token_values": {}},
        ):
            real_time_data = await data_analysis_service._get_real_time_data(
                "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
            )

            assert "balances" in real_time_data
            assert "defi_positions" in real_time_data
            assert "portfolio_value" in real_time_data
            assert "last_updated" in real_time_data

    @pytest.mark.asyncio
    async def test_get_historical_analysis(self, data_analysis_service):
        """Test getting historical analysis."""
        mock_timeline = PortfolioTimeline(
            timestamps=[], collateral_usd=[], borrowings_usd=[]
        )

        with patch.object(
            data_analysis_service.portfolio_service,
            "calculate_portfolio_timeline",
            return_value=mock_timeline,
        ), patch.object(
            data_analysis_service.blockchain_service,
            "get_historical_data",
            return_value=[{"timestamp": 1234567890, "portfolio_value": 28000.0}],
        ):
            historical_analysis = await data_analysis_service._get_historical_analysis(
                "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
            )

            assert "timeline" in historical_analysis
            assert "historical_data" in historical_analysis
            assert "analysis_period" in historical_analysis
            assert "data_points" in historical_analysis

    @pytest.mark.asyncio
    async def test_generate_predictions(self, data_analysis_service):
        """Test generating predictions."""
        mock_historical_data = [
            {"portfolio_value": 28000.0},
            {"portfolio_value": 29000.0},
            {"portfolio_value": 28500.0},
        ]

        with patch.object(
            data_analysis_service.blockchain_service,
            "get_historical_data",
            return_value=mock_historical_data,
        ):
            predictions = await data_analysis_service._generate_predictions(
                "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
            )

            assert "predictions" in predictions
            assert "trend" in predictions
            assert "confidence" in predictions
            assert len(predictions["predictions"]) > 0

    @pytest.mark.asyncio
    async def test_generate_predictions_no_data(self, data_analysis_service):
        """Test generating predictions with no historical data."""
        with patch.object(
            data_analysis_service.blockchain_service,
            "get_historical_data",
            return_value=[],
        ):
            predictions = await data_analysis_service._generate_predictions(
                "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
            )

            assert predictions["predictions"] == []
            assert predictions["confidence"] == 0.0

    @pytest.mark.asyncio
    async def test_get_token_historical_data(self, data_analysis_service):
        """Test getting token historical data."""
        historical_data = await data_analysis_service._get_token_historical_data(
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", 30
        )

        assert len(historical_data) > 0
        assert all("timestamp" in point for point in historical_data)
        assert all("price" in point for point in historical_data)
        assert all("volume" in point for point in historical_data)

    def test_calculate_trend_metrics(self, data_analysis_service):
        """Test calculating trend metrics."""
        historical_data = [{"price": 100.0}, {"price": 110.0}, {"price": 105.0}]

        metrics = data_analysis_service._calculate_trend_metrics(historical_data)

        assert "total_return" in metrics
        assert "volatility" in metrics
        assert "trend_strength" in metrics
        assert "start_price" in metrics
        assert "end_price" in metrics
        assert "price_change" in metrics

        assert metrics["start_price"] == 100.0
        assert metrics["end_price"] == 105.0
        assert metrics["price_change"] == 5.0
        assert metrics["total_return"] == 0.05  # (105-100)/100

    def test_calculate_trend_metrics_insufficient_data(self, data_analysis_service):
        """Test calculating trend metrics with insufficient data."""
        historical_data = [{"price": 100.0}]  # Only one data point

        metrics = data_analysis_service._calculate_trend_metrics(historical_data)

        assert metrics == {}

    def test_calculate_market_sentiment_bullish(self, data_analysis_service):
        """Test calculating bullish market sentiment."""
        trends = {
            "token1": {"total_return": 0.1},
            "token2": {"total_return": 0.2},
            "token3": {"total_return": 0.15},
        }

        sentiment = data_analysis_service._calculate_market_sentiment(trends)

        assert sentiment == "bullish"  # All positive returns

    def test_calculate_market_sentiment_bearish(self, data_analysis_service):
        """Test calculating bearish market sentiment."""
        trends = {
            "token1": {"total_return": -0.1},
            "token2": {"total_return": -0.2},
            "token3": {"total_return": -0.15},
        }

        sentiment = data_analysis_service._calculate_market_sentiment(trends)

        assert sentiment == "bearish"  # All negative returns

    def test_calculate_market_sentiment_neutral(self, data_analysis_service):
        """Test calculating neutral market sentiment."""
        trends = {
            "token1": {"total_return": 0.1},
            "token2": {"total_return": -0.1},
            "token3": {"total_return": 0.05},
        }

        sentiment = data_analysis_service._calculate_market_sentiment(trends)

        assert sentiment == "neutral"  # Mixed returns

    def test_calculate_market_sentiment_empty(self, data_analysis_service):
        """Test calculating market sentiment with empty trends."""
        sentiment = data_analysis_service._calculate_market_sentiment({})

        assert sentiment == "neutral"

    def test_create_empty_analysis(self, data_analysis_service):
        """Test creating empty analysis result."""
        analysis = data_analysis_service._create_empty_analysis(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        )

        assert analysis["user_address"] == "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        assert analysis["error"] == "Analysis failed"
        assert analysis["portfolio_metrics"] is None
        assert analysis["real_time_data"] is None
        assert analysis["historical_analysis"] is None
        assert analysis["risk_assessment"] is None
        assert analysis["performance_metrics"] is None
        assert analysis["predictions"] is None
