"""
Unit tests for DataAnalysisService.

Tests the simplified portfolio dashboard functionality.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.data_analysis_service import DataAnalysisService


class TestDataAnalysisService:
    """Test cases for DataAnalysisService."""

    @pytest.fixture
    def data_analysis_service(self, db_session):
        """Create a DataAnalysisService instance for testing."""
        return DataAnalysisService(db_session)

    @pytest.fixture
    def mock_portfolio_metrics(self):
        """Mock portfolio metrics."""
        metrics = MagicMock()
        metrics.aggregate_health_score = 0.85
        metrics.aggregate_apy = 0.12
        metrics.total_value_locked = 50000.0
        metrics.total_borrowed = 10000.0
        return metrics

    async def test_get_portfolio_dashboard_success(
        self, data_analysis_service, mock_portfolio_metrics
    ):
        """Test successful portfolio dashboard retrieval."""
        # Mock portfolio service methods
        data_analysis_service.portfolio_service.calculate_portfolio_metrics = AsyncMock(
            return_value=mock_portfolio_metrics
        )
        data_analysis_service.portfolio_service.calculate_risk_metrics = AsyncMock(
            return_value={"utilization_rate": 0.2, "health_score": 0.85}
        )
        data_analysis_service.portfolio_service.calculate_performance_metrics = (
            MagicMock(return_value={"total_return": 0.15, "sharpe_ratio": 1.2})
        )

        # Mock blockchain service methods
        data_analysis_service.blockchain_service.get_defi_positions = AsyncMock(
            return_value=[{"protocol": "Aave", "value": 50000}]
        )
        data_analysis_service.blockchain_service.get_portfolio_value = AsyncMock(
            return_value=50000.0
        )

        # Test dashboard retrieval
        dashboard = await data_analysis_service.get_portfolio_dashboard(
            "0x1234567890abcdef"
        )

        # Verify structure
        assert dashboard["user_address"] == "0x1234567890abcdef"
        assert dashboard["portfolio_metrics"] == mock_portfolio_metrics
        assert dashboard["risk_metrics"] == {
            "utilization_rate": 0.2,
            "health_score": 0.85,
        }
        assert dashboard["performance_metrics"] == {
            "total_return": 0.15,
            "sharpe_ratio": 1.2,
        }
        assert "real_time_data" in dashboard
        assert "timestamp" in dashboard

    async def test_get_portfolio_dashboard_error_handling(self, data_analysis_service):
        """Test error handling in portfolio dashboard retrieval."""
        # Mock portfolio service to raise exception
        data_analysis_service.portfolio_service.calculate_portfolio_metrics = AsyncMock(
            side_effect=Exception("Database error")
        )

        # Test dashboard retrieval with error
        dashboard = await data_analysis_service.get_portfolio_dashboard(
            "0x1234567890abcdef"
        )

        # Verify error response
        assert dashboard["user_address"] == "0x1234567890abcdef"
        assert dashboard["error"] == "Dashboard data unavailable"
        assert dashboard["portfolio_metrics"] is None
        assert dashboard["real_time_data"] is None
        assert dashboard["risk_metrics"] is None
        assert dashboard["performance_metrics"] is None

    async def test_get_real_time_data(self, data_analysis_service):
        """Test real-time data retrieval."""
        # Mock blockchain service methods
        data_analysis_service.blockchain_service.get_defi_positions = AsyncMock(
            return_value=[{"protocol": "Aave", "value": 50000}]
        )
        data_analysis_service.blockchain_service.get_portfolio_value = AsyncMock(
            return_value=50000.0
        )

        # Test real-time data retrieval
        real_time_data = await data_analysis_service._get_real_time_data(
            "0x1234567890abcdef"
        )

        # Verify structure
        assert "defi_positions" in real_time_data
        assert "portfolio_value" in real_time_data
        assert "last_updated" in real_time_data
        assert real_time_data["defi_positions"] == [
            {"protocol": "Aave", "value": 50000}
        ]
        assert real_time_data["portfolio_value"] == 50000.0

    async def test_get_real_time_data_error_handling(self, data_analysis_service):
        """Test error handling in real-time data retrieval."""
        # Mock blockchain service to raise exception
        data_analysis_service.blockchain_service.get_defi_positions = AsyncMock(
            side_effect=Exception("Blockchain error")
        )

        # Test real-time data retrieval with error
        real_time_data = await data_analysis_service._get_real_time_data(
            "0x1234567890abcdef"
        )

        # Verify empty response
        assert real_time_data == {}

    def test_create_empty_dashboard(self, data_analysis_service):
        """Test empty dashboard creation."""
        dashboard = data_analysis_service._create_empty_dashboard("0x1234567890abcdef")

        # Verify structure
        assert dashboard["user_address"] == "0x1234567890abcdef"
        assert dashboard["error"] == "Dashboard data unavailable"
        assert dashboard["portfolio_metrics"] is None
        assert dashboard["real_time_data"] is None
        assert dashboard["risk_metrics"] is None
        assert dashboard["performance_metrics"] is None
        assert "timestamp" in dashboard
