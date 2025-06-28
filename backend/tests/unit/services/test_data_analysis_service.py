"""
Unit tests for DataAnalysisService.

Tests the simplified portfolio dashboard functionality.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from app.services.data_analysis_service import DataAnalysisService


class TestDataAnalysisService:
    """Test cases for DataAnalysisService."""

    @pytest.fixture(scope="function")
    def data_analysis_service(self, db_session):
        """Create a DataAnalysisService instance for testing."""
        return DataAnalysisService(db_session)

    @pytest.fixture(scope="function")
    def mock_portfolio_metrics(self):
        """Mock portfolio metrics."""
        metrics = MagicMock()
        metrics.aggregate_balance = 10000.0
        metrics.total_pnl = 500.0
        metrics.total_pnl_percentage = 5.0
        metrics.daily_pnl = 50.0
        metrics.daily_pnl_percentage = 0.5
        metrics.weekly_pnl = 200.0
        metrics.weekly_pnl_percentage = 2.0
        metrics.monthly_pnl = 800.0
        metrics.monthly_pnl_percentage = 8.0
        return metrics

    @pytest.fixture(scope="function")
    def mock_risk_metrics(self):
        """Mock risk metrics."""
        return {
            "utilization_rate": 0.2,
            "health_score": 0.85,
        }

    @pytest.fixture(scope="function")
    def mock_performance_metrics(self):
        """Mock performance metrics."""
        return {
            "total_return": 0.15,
            "sharpe_ratio": 1.2,
        }

    @pytest.fixture(scope="function")
    def mock_real_time_data(self):
        """Mock real-time data."""
        return {
            "defi_positions": [{"protocol": "Aave", "value": 50000}],
            "portfolio_value": 50000.0,
            "last_updated": datetime.utcnow(),
        }

    @pytest.fixture(scope="function")
    def mock_token_balances(self):
        """Mock token balances."""
        return [
            {
                "token_address": "0x1234567890123456789012345678901234567890",
                "token_symbol": "USDC",
                "balance": 5000.0,
                "usd_value": 5000.0,
                "price": 1.0,
            },
            {
                "token_address": "0x0987654321098765432109876543210987654321",
                "token_symbol": "ETH",
                "balance": 2.5,
                "usd_value": 5000.0,
                "price": 2000.0,
            },
        ]

    @pytest.fixture(scope="function")
    def mock_recent_transactions(self):
        """Mock recent transactions."""
        return [
            {
                "hash": "0xabc123",
                "timestamp": datetime.now(),
                "type": "swap",
                "token_in": "USDC",
                "token_out": "ETH",
                "amount_in": 1000.0,
                "amount_out": 0.5,
                "usd_value": 1000.0,
            },
            {
                "hash": "0xdef456",
                "timestamp": datetime.now(),
                "type": "transfer",
                "token_in": "ETH",
                "token_out": "USDC",
                "amount_in": 0.25,
                "amount_out": 500.0,
                "usd_value": 500.0,
            },
        ]

    @pytest.mark.asyncio
    async def test_get_portfolio_dashboard_success(
        self,
        data_analysis_service,
        mock_portfolio_metrics,
        mock_risk_metrics,
        mock_performance_metrics,
        mock_real_time_data,
    ):
        """Test successful portfolio dashboard retrieval."""
        user_address = "0x1234567890abcdef"

        # Mock the service methods
        with patch.object(
            data_analysis_service.portfolio_service,
            "calculate_portfolio_metrics",
            return_value=mock_portfolio_metrics,
        ), patch.object(
            data_analysis_service.portfolio_service,
            "calculate_risk_metrics",
            return_value=mock_risk_metrics,
        ), patch.object(
            data_analysis_service.portfolio_service,
            "calculate_performance_metrics",
            return_value=mock_performance_metrics,
        ), patch.object(
            data_analysis_service,
            "_get_real_time_data",
            return_value=mock_real_time_data,
        ):
            result = await data_analysis_service.get_portfolio_dashboard(user_address)

        # Verify the result structure
        assert result is not None
        assert result["user_address"] == user_address
        assert "timestamp" in result
        assert "portfolio_metrics" in result
        assert "real_time_data" in result
        assert "risk_metrics" in result
        assert "performance_metrics" in result

        # Verify portfolio metrics
        assert result["portfolio_metrics"] == mock_portfolio_metrics

        # Verify risk metrics
        assert result["risk_metrics"] == mock_risk_metrics

        # Verify performance metrics
        assert result["performance_metrics"] == mock_performance_metrics

        # Verify real-time data
        assert result["real_time_data"] == mock_real_time_data

    @pytest.mark.asyncio
    async def test_get_portfolio_dashboard_empty_data(self, data_analysis_service):
        """Test portfolio dashboard with empty data."""
        user_address = "0x1234567890abcdef"

        # Mock empty responses
        with patch.object(
            data_analysis_service.portfolio_service,
            "calculate_portfolio_metrics",
            return_value=None,
        ), patch.object(
            data_analysis_service.portfolio_service,
            "calculate_risk_metrics",
            return_value=None,
        ), patch.object(
            data_analysis_service.portfolio_service,
            "calculate_performance_metrics",
            return_value=None,
        ), patch.object(
            data_analysis_service,
            "_get_real_time_data",
            return_value={},
        ):
            result = await data_analysis_service.get_portfolio_dashboard(user_address)

        # Verify the result structure with empty data
        assert result is not None
        assert result["user_address"] == user_address
        assert "timestamp" in result
        assert "portfolio_metrics" in result
        assert "real_time_data" in result
        assert "risk_metrics" in result
        assert "performance_metrics" in result

        # Verify empty data
        assert result["portfolio_metrics"] is None
        assert result["real_time_data"] == {}
        assert result["risk_metrics"] is None
        assert result["performance_metrics"] is None

    @pytest.mark.asyncio
    async def test_get_portfolio_dashboard_exception_handling(
        self, data_analysis_service
    ):
        """Test portfolio dashboard handles exceptions gracefully."""
        user_address = "0x1234567890abcdef"

        # Mock service to raise exception
        with patch.object(
            data_analysis_service.portfolio_service,
            "calculate_portfolio_metrics",
            side_effect=Exception("Service error"),
        ):
            result = await data_analysis_service.get_portfolio_dashboard(user_address)

        # Verify error handling
        assert result is not None
        assert result["user_address"] == user_address
        assert "timestamp" in result
        assert "error" in result
        assert result["error"] == "Dashboard data unavailable"
        assert result["portfolio_metrics"] is None
        assert result["real_time_data"] is None
        assert result["risk_metrics"] is None
        assert result["performance_metrics"] is None

    @pytest.mark.asyncio
    async def test_get_real_time_data_success(self, data_analysis_service):
        """Test successful real-time data retrieval."""
        user_address = "0x1234567890abcdef"
        mock_defi_positions = [{"protocol": "Aave", "value": 50000}]
        mock_portfolio_value = 50000.0

        with patch.object(
            data_analysis_service.blockchain_service,
            "get_defi_positions",
            return_value=mock_defi_positions,
        ), patch.object(
            data_analysis_service.blockchain_service,
            "calculate_portfolio_value",
            return_value=mock_portfolio_value,
        ):
            result = await data_analysis_service._get_real_time_data(user_address)

        assert result is not None
        assert "defi_positions" in result
        assert "portfolio_value" in result
        assert "last_updated" in result
        assert result["defi_positions"] == mock_defi_positions
        assert result["portfolio_value"] == mock_portfolio_value

    @pytest.mark.asyncio
    async def test_get_real_time_data_exception_handling(self, data_analysis_service):
        """Test real-time data handles exceptions gracefully."""
        user_address = "0x1234567890abcdef"

        with patch.object(
            data_analysis_service.blockchain_service,
            "get_defi_positions",
            side_effect=Exception("Blockchain error"),
        ):
            result = await data_analysis_service._get_real_time_data(user_address)

        assert result == {}

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
        """Test real-time data returns empty dict for portfolio_value when no data."""
        user_address = "0x1234567890abcdef"
        mock_defi_positions = []
        mock_portfolio_value = {"total_value": 0.0, "token_values": {}}

        with patch.object(
            data_analysis_service.blockchain_service,
            "get_defi_positions",
            return_value=mock_defi_positions,
        ), patch.object(
            data_analysis_service.blockchain_service,
            "calculate_portfolio_value",
            return_value=mock_portfolio_value,
        ):
            real_time_data = await data_analysis_service._get_real_time_data(
                user_address
            )

        assert real_time_data["defi_positions"] == mock_defi_positions
        assert real_time_data["portfolio_value"] == mock_portfolio_value
        assert "last_updated" in real_time_data

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
        data_analysis_service.blockchain_service.calculate_portfolio_value = AsyncMock(
            return_value={
                "total_value": 80000.0,
                "token_values": {"USDC": 50000.0, "USDT": 30000.0},
            }
        )

        # Test real-time data retrieval
        real_time_data = await data_analysis_service._get_real_time_data(
            "0x1234567890abcdef"
        )

        # Verify structure
        assert len(real_time_data["defi_positions"]) == 2
        assert real_time_data["portfolio_value"]["total_value"] == 80000.0
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
