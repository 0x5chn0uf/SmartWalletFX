"""
Unit tests for DataAnalysisService.

Tests the simplified portfolio dashboard functionality.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock

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

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_get_portfolio_dashboard_partial_error_handling(
        self, data_analysis_service
    ):
        """Test error handling when only some services fail."""
        # Mock portfolio service to succeed
        data_analysis_service.portfolio_service.calculate_portfolio_metrics = AsyncMock(
            return_value=MagicMock()
        )
        data_analysis_service.portfolio_service.calculate_risk_metrics = AsyncMock(
            return_value={"utilization_rate": 0.2}
        )
        data_analysis_service.portfolio_service.calculate_performance_metrics = (
            MagicMock(return_value={"total_return": 0.15})
        )

        # Mock blockchain service to fail
        data_analysis_service.blockchain_service.get_defi_positions = AsyncMock(
            side_effect=Exception("Blockchain error")
        )
        data_analysis_service.blockchain_service.get_portfolio_value = AsyncMock(
            side_effect=Exception("Blockchain error")
        )

        # Test dashboard retrieval with partial error
        dashboard = await data_analysis_service.get_portfolio_dashboard(
            "0x1234567890abcdef"
        )

        # Should still succeed but with empty real-time data
        assert dashboard["user_address"] == "0x1234567890abcdef"
        assert dashboard["portfolio_metrics"] is not None
        assert dashboard["risk_metrics"] is not None
        assert dashboard["performance_metrics"] is not None
        assert dashboard["real_time_data"] == {}

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_get_real_time_data_partial_error_handling(
        self, data_analysis_service
    ):
        """Test error handling when only some blockchain methods fail."""
        # Mock one method to succeed, one to fail
        data_analysis_service.blockchain_service.get_defi_positions = AsyncMock(
            return_value=[{"protocol": "Aave", "value": 50000}]
        )
        data_analysis_service.blockchain_service.get_portfolio_value = AsyncMock(
            side_effect=Exception("Portfolio value error")
        )

        # Test real-time data retrieval with partial error
        real_time_data = await data_analysis_service._get_real_time_data(
            "0x1234567890abcdef"
        )

        # Should return empty dict due to any error
        assert real_time_data == {}

    @pytest.mark.asyncio
    async def test_get_real_time_data_empty_positions(self, data_analysis_service):
        """Test real-time data retrieval with empty DeFi positions."""
        # Mock blockchain service methods
        data_analysis_service.blockchain_service.get_defi_positions = AsyncMock(
            return_value=[]
        )
        data_analysis_service.blockchain_service.get_portfolio_value = AsyncMock(
            return_value=0.0
        )

        # Test real-time data retrieval
        real_time_data = await data_analysis_service._get_real_time_data(
            "0x1234567890abcdef"
        )

        # Verify structure
        assert "defi_positions" in real_time_data
        assert "portfolio_value" in real_time_data
        assert "last_updated" in real_time_data
        assert real_time_data["defi_positions"] == []
        assert real_time_data["portfolio_value"] == 0.0

    @pytest.mark.asyncio
    async def test_get_real_time_data_multiple_protocols(self, data_analysis_service):
        """Test real-time data retrieval with multiple protocols."""
        # Mock blockchain service methods
        data_analysis_service.blockchain_service.get_defi_positions = AsyncMock(
            return_value=[
                {"protocol": "Aave", "value": 30000},
                {"protocol": "Compound", "value": 20000},
                {"protocol": "Maker", "value": 10000},
            ]
        )
        data_analysis_service.blockchain_service.get_portfolio_value = AsyncMock(
            return_value=60000.0
        )

        # Test real-time data retrieval
        real_time_data = await data_analysis_service._get_real_time_data(
            "0x1234567890abcdef"
        )

        # Verify structure
        assert len(real_time_data["defi_positions"]) == 3
        assert real_time_data["portfolio_value"] == 60000.0
        assert real_time_data["defi_positions"][0]["protocol"] == "Aave"
        assert real_time_data["defi_positions"][1]["protocol"] == "Compound"
        assert real_time_data["defi_positions"][2]["protocol"] == "Maker"

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    def test_create_empty_dashboard_different_address(self, data_analysis_service):
        """Test empty dashboard creation with different address."""
        dashboard = data_analysis_service._create_empty_dashboard("0xfedcba0987654321")

        # Verify structure
        assert dashboard["user_address"] == "0xfedcba0987654321"
        assert dashboard["error"] == "Dashboard data unavailable"
        assert dashboard["portfolio_metrics"] is None
        assert dashboard["real_time_data"] is None
        assert dashboard["risk_metrics"] is None
        assert dashboard["performance_metrics"] is None
        assert "timestamp" in dashboard

    @pytest.mark.asyncio
    def test_data_analysis_service_initialization(self, db_session):
        """Test DataAnalysisService initialization."""
        service = DataAnalysisService(db_session)

        assert service.db == db_session
        assert service.portfolio_service is not None
        assert service.blockchain_service is not None
        assert service.portfolio_service.db == db_session

    @pytest.mark.asyncio
    async def test_get_portfolio_dashboard_with_none_metrics(
        self, data_analysis_service
    ):
        """Test portfolio dashboard with None metrics."""
        # Mock portfolio service methods to return None
        data_analysis_service.portfolio_service.calculate_portfolio_metrics = AsyncMock(
            return_value=None
        )
        data_analysis_service.portfolio_service.calculate_risk_metrics = AsyncMock(
            return_value=None
        )
        data_analysis_service.portfolio_service.calculate_performance_metrics = (
            MagicMock(return_value=None)
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

        # Verify structure with None values
        assert dashboard["user_address"] == "0x1234567890abcdef"
        assert dashboard["portfolio_metrics"] is None
        assert dashboard["risk_metrics"] is None
        assert dashboard["performance_metrics"] is None
        assert "real_time_data" in dashboard
        assert "timestamp" in dashboard

    @pytest.mark.asyncio
    async def test_get_portfolio_dashboard_with_empty_string_address(
        self, data_analysis_service
    ):
        """Test portfolio dashboard with empty string address."""
        # Mock all services to succeed
        data_analysis_service.portfolio_service.calculate_portfolio_metrics = AsyncMock(
            return_value=MagicMock()
        )
        data_analysis_service.portfolio_service.calculate_risk_metrics = AsyncMock(
            return_value={"utilization_rate": 0.2}
        )
        data_analysis_service.portfolio_service.calculate_performance_metrics = (
            MagicMock(return_value={"total_return": 0.15})
        )
        data_analysis_service.blockchain_service.get_defi_positions = AsyncMock(
            return_value=[]
        )
        data_analysis_service.blockchain_service.get_portfolio_value = AsyncMock(
            return_value=0.0
        )

        # Test with empty string address
        dashboard = await data_analysis_service.get_portfolio_dashboard("")

        # Verify structure
        assert dashboard["user_address"] == ""
        assert dashboard["portfolio_metrics"] is not None
        assert dashboard["risk_metrics"] is not None
        assert dashboard["performance_metrics"] is not None
        assert "real_time_data" in dashboard
        assert "timestamp" in dashboard

    @pytest.mark.asyncio
    async def test_get_portfolio_dashboard_with_special_characters_address(
        self, data_analysis_service
    ):
        """Test portfolio dashboard with address containing special characters."""
        # Mock all services to succeed
        data_analysis_service.portfolio_service.calculate_portfolio_metrics = AsyncMock(
            return_value=MagicMock()
        )
        data_analysis_service.portfolio_service.calculate_risk_metrics = AsyncMock(
            return_value={"utilization_rate": 0.2}
        )
        data_analysis_service.portfolio_service.calculate_performance_metrics = (
            MagicMock(return_value={"total_return": 0.15})
        )
        data_analysis_service.blockchain_service.get_defi_positions = AsyncMock(
            return_value=[]
        )
        data_analysis_service.blockchain_service.get_portfolio_value = AsyncMock(
            return_value=0.0
        )

        # Test with special characters in address
        special_address = "0x1234567890abcdef!@#$%^&*()"
        dashboard = await data_analysis_service.get_portfolio_dashboard(special_address)

        # Verify structure
        assert dashboard["user_address"] == special_address
        assert dashboard["portfolio_metrics"] is not None
        assert dashboard["risk_metrics"] is not None
        assert dashboard["performance_metrics"] is not None
        assert "real_time_data" in dashboard
        assert "timestamp" in dashboard

    @pytest.mark.asyncio
    async def test_get_real_time_data_with_none_values(self, data_analysis_service):
        """Test real-time data retrieval with None values from blockchain service."""
        # Mock blockchain service methods to return None
        data_analysis_service.blockchain_service.get_defi_positions = AsyncMock(
            return_value=None
        )
        data_analysis_service.blockchain_service.get_portfolio_value = AsyncMock(
            return_value=None
        )

        # Test real-time data retrieval
        real_time_data = await data_analysis_service._get_real_time_data(
            "0x1234567890abcdef"
        )

        # Verify structure with None values
        assert "defi_positions" in real_time_data
        assert "portfolio_value" in real_time_data
        assert "last_updated" in real_time_data
        assert real_time_data["defi_positions"] is None
        assert real_time_data["portfolio_value"] is None

    @pytest.mark.asyncio
    async def test_get_real_time_data_with_complex_positions(
        self, data_analysis_service
    ):
        """Test real-time data retrieval with complex position data."""
        complex_positions = [
            {
                "protocol": "Aave",
                "value": 50000.0,
                "tokens": ["USDC", "DAI"],
                "apy": 0.08,
                "collateral": True,
            },
            {
                "protocol": "Compound",
                "value": 30000.0,
                "tokens": ["USDT"],
                "apy": 0.05,
                "collateral": False,
            },
        ]

        # Mock blockchain service methods
        data_analysis_service.blockchain_service.get_defi_positions = AsyncMock(
            return_value=complex_positions
        )
        data_analysis_service.blockchain_service.get_portfolio_value = AsyncMock(
            return_value=80000.0
        )

        # Test real-time data retrieval
        real_time_data = await data_analysis_service._get_real_time_data(
            "0x1234567890abcdef"
        )

        # Verify structure
        assert len(real_time_data["defi_positions"]) == 2
        assert real_time_data["portfolio_value"] == 80000.0
        assert real_time_data["defi_positions"][0]["protocol"] == "Aave"
        assert real_time_data["defi_positions"][0]["tokens"] == ["USDC", "DAI"]
        assert real_time_data["defi_positions"][1]["protocol"] == "Compound"
        assert real_time_data["defi_positions"][1]["tokens"] == ["USDT"]

    def test_create_empty_dashboard_timestamp_format(self, data_analysis_service):
        """Test that empty dashboard timestamp is a datetime object."""
        dashboard = data_analysis_service._create_empty_dashboard("0x1234567890abcdef")

        # Verify timestamp is a datetime object
        assert isinstance(dashboard["timestamp"], datetime)

        # Verify timestamp is recent (within last minute)
        now = datetime.utcnow()
        time_diff = abs((now - dashboard["timestamp"]).total_seconds())
        assert time_diff < 60  # Should be within 60 seconds

    @pytest.mark.asyncio
    async def test_get_portfolio_dashboard_timestamp_format(
        self, data_analysis_service
    ):
        """Test that dashboard timestamp is a datetime object."""
        # Mock all services to succeed
        data_analysis_service.portfolio_service.calculate_portfolio_metrics = AsyncMock(
            return_value=MagicMock()
        )
        data_analysis_service.portfolio_service.calculate_risk_metrics = AsyncMock(
            return_value={"utilization_rate": 0.2}
        )
        data_analysis_service.portfolio_service.calculate_performance_metrics = (
            MagicMock(return_value={"total_return": 0.15})
        )
        data_analysis_service.blockchain_service.get_defi_positions = AsyncMock(
            return_value=[]
        )
        data_analysis_service.blockchain_service.get_portfolio_value = AsyncMock(
            return_value=0.0
        )

        # Test dashboard retrieval
        dashboard = await data_analysis_service.get_portfolio_dashboard(
            "0x1234567890abcdef"
        )

        # Verify timestamp is a datetime object
        assert isinstance(dashboard["timestamp"], datetime)

        # Verify timestamp is recent (within last minute)
        now = datetime.utcnow()
        time_diff = abs((now - dashboard["timestamp"]).total_seconds())
        assert time_diff < 60  # Should be within 60 seconds

    @pytest.mark.asyncio
    async def test_get_real_time_data_timestamp_format(self, data_analysis_service):
        """Test that real-time data timestamp is a datetime object."""
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

        # Verify timestamp is a datetime object
        assert isinstance(real_time_data["last_updated"], datetime)

        # Verify timestamp is recent (within last minute)
        now = datetime.utcnow()
        time_diff = abs((now - real_time_data["last_updated"]).total_seconds())
        assert time_diff < 60  # Should be within 60 seconds

    @pytest.mark.asyncio
    async def test_get_portfolio_dashboard_all_services_fail(
        self, data_analysis_service
    ):
        """Test dashboard when all services fail."""
        # Mock all services to fail
        data_analysis_service.portfolio_service.calculate_portfolio_metrics = AsyncMock(
            side_effect=Exception("Portfolio service error")
        )
        data_analysis_service.portfolio_service.calculate_risk_metrics = AsyncMock(
            side_effect=Exception("Risk service error")
        )
        data_analysis_service.portfolio_service.calculate_performance_metrics = (
            MagicMock(side_effect=Exception("Performance service error"))
        )
        data_analysis_service.blockchain_service.get_defi_positions = AsyncMock(
            side_effect=Exception("Blockchain service error")
        )
        data_analysis_service.blockchain_service.get_portfolio_value = AsyncMock(
            side_effect=Exception("Portfolio value error")
        )

        # Test dashboard retrieval
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
