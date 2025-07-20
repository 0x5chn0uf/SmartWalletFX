"""Unit tests for WalletUsecase missing coverage areas."""

import time
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException, status

from app.domain.schemas.defi import ProtocolName
from app.domain.schemas.portfolio_metrics import (
    PortfolioMetrics,
    ProtocolBreakdown,
)
from app.domain.schemas.portfolio_timeline import PortfolioTimeline
from app.domain.schemas.wallet import WalletCreate, WalletResponse


class TestWalletUsecaseMissingCoverage:
    """Test missing coverage areas in WalletUsecase."""

    @pytest.mark.asyncio
    async def test_create_wallet_user_not_found(self, wallet_usecase_with_di):
        """Test create_wallet when user is not found."""
        usecase = wallet_usecase_with_di
        user_id = uuid.uuid4()
        wallet_create = WalletCreate(
            address="0x1234567890123456789012345678901234567890", name="Test Wallet"
        )

        # Mock user not found
        usecase._WalletUsecase__user_repo.get_by_id = AsyncMock(return_value=None)

        # Execute and verify exception
        with pytest.raises(HTTPException) as exc_info:
            await usecase.create_wallet(user_id, wallet_create)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in str(exc_info.value.detail)

        # Verify user repo was called
        usecase._WalletUsecase__user_repo.get_by_id.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_create_wallet_exception_handling(self, wallet_usecase_with_di):
        """Test create_wallet exception handling."""
        usecase = wallet_usecase_with_di
        user_id = uuid.uuid4()
        wallet_create = WalletCreate(
            address="0x1234567890123456789012345678901234567890", name="Test Wallet"
        )

        # Mock user exists
        user = Mock()
        user.id = user_id
        usecase._WalletUsecase__user_repo.get_by_id = AsyncMock(return_value=user)

        # Mock wallet repository exception
        usecase._WalletUsecase__wallet_repo.create = AsyncMock(
            side_effect=Exception("Database error")
        )

        # Execute and verify exception
        with pytest.raises(Exception, match="Database error"):
            await usecase.create_wallet(user_id, wallet_create)

        # Verify audit error was called
        usecase._WalletUsecase__audit.error.assert_called_once()
        error_call = usecase._WalletUsecase__audit.error.call_args
        assert error_call[0][0] == "wallet_usecase_create_wallet_failed"
        assert "Database error" in error_call[1]["error"]

    @pytest.mark.asyncio
    async def test_list_wallets_user_not_found(self, wallet_usecase_with_di):
        """Test list_wallets when user is not found."""
        usecase = wallet_usecase_with_di
        user_id = uuid.uuid4()

        # Mock user not found
        usecase._WalletUsecase__user_repo.get_by_id = AsyncMock(return_value=None)

        # Execute and verify exception
        with pytest.raises(HTTPException) as exc_info:
            await usecase.list_wallets(user_id)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_list_wallets_exception_handling(self, wallet_usecase_with_di):
        """Test list_wallets exception handling."""
        usecase = wallet_usecase_with_di
        user_id = uuid.uuid4()

        # Mock user exists
        user = Mock()
        user.id = user_id
        usecase._WalletUsecase__user_repo.get_by_id = AsyncMock(return_value=user)

        # Mock wallet repository exception
        usecase._WalletUsecase__wallet_repo.list_by_user = AsyncMock(
            side_effect=Exception("Database error")
        )

        # Execute and verify exception
        with pytest.raises(Exception, match="Database error"):
            await usecase.list_wallets(user_id)

        # Verify audit error was called
        usecase._WalletUsecase__audit.error.assert_called_once()
        error_call = usecase._WalletUsecase__audit.error.call_args
        assert error_call[0][0] == "wallet_usecase_list_wallets_failed"
        assert "Database error" in error_call[1]["error"]

    @pytest.mark.asyncio
    async def test_delete_wallet_user_not_found(self, wallet_usecase_with_di):
        """Test delete_wallet when user is not found."""
        usecase = wallet_usecase_with_di
        user_id = uuid.uuid4()
        address = "0x1234567890123456789012345678901234567890"

        # Mock user not found
        usecase._WalletUsecase__user_repo.get_by_id = AsyncMock(return_value=None)

        # Execute and verify exception
        with pytest.raises(HTTPException) as exc_info:
            await usecase.delete_wallet(user_id, address)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_delete_wallet_exception_handling(self, wallet_usecase_with_di):
        """Test delete_wallet exception handling."""
        usecase = wallet_usecase_with_di
        user_id = uuid.uuid4()
        address = "0x1234567890123456789012345678901234567890"

        # Mock user exists
        user = Mock()
        user.id = user_id
        usecase._WalletUsecase__user_repo.get_by_id = AsyncMock(return_value=user)

        # Mock wallet repository exception
        usecase._WalletUsecase__wallet_repo.delete = AsyncMock(
            side_effect=Exception("Database error")
        )

        # Execute and verify exception
        with pytest.raises(Exception, match="Database error"):
            await usecase.delete_wallet(user_id, address)

        # Verify audit error was called
        usecase._WalletUsecase__audit.error.assert_called_once()
        error_call = usecase._WalletUsecase__audit.error.call_args
        assert error_call[0][0] == "wallet_usecase_delete_wallet_failed"
        assert "Database error" in error_call[1]["error"]

    @pytest.mark.asyncio
    async def test_verify_wallet_ownership_user_not_found(self, wallet_usecase_with_di):
        """Test verify_wallet_ownership when user is not found."""
        usecase = wallet_usecase_with_di
        user_id = uuid.uuid4()
        address = "0x1234567890123456789012345678901234567890"

        # Mock user not found
        usecase._WalletUsecase__user_repo.get_by_id = AsyncMock(return_value=None)

        # Execute
        result = await usecase.verify_wallet_ownership(user_id, address)

        # Verify returns False
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_wallet_ownership_exception_handling(
        self, wallet_usecase_with_di
    ):
        """Test verify_wallet_ownership exception handling."""
        usecase = wallet_usecase_with_di
        user_id = uuid.uuid4()
        address = "0x1234567890123456789012345678901234567890"

        # Mock user exists
        user = Mock()
        user.id = user_id
        usecase._WalletUsecase__user_repo.get_by_id = AsyncMock(return_value=user)

        # Mock wallet repository exception
        usecase._WalletUsecase__wallet_repo.get_by_address = AsyncMock(
            side_effect=Exception("Database error")
        )

        # Execute and verify exception
        with pytest.raises(Exception, match="Database error"):
            await usecase.verify_wallet_ownership(user_id, address)

        # Verify audit error was called
        usecase._WalletUsecase__audit.error.assert_called_once()
        error_call = usecase._WalletUsecase__audit.error.call_args
        assert error_call[0][0] == "wallet_usecase_verify_ownership_failed"
        assert "Database error" in error_call[1]["error"]

    @pytest.mark.asyncio
    async def test_get_portfolio_snapshots_user_not_found(self, wallet_usecase_with_di):
        """Test get_portfolio_snapshots when user is not found."""
        usecase = wallet_usecase_with_di
        user_id = uuid.uuid4()
        address = "0x1234567890123456789012345678901234567890"

        # Mock user not found
        usecase._WalletUsecase__user_repo.get_by_id = AsyncMock(return_value=None)

        # Execute and verify exception
        with pytest.raises(HTTPException) as exc_info:
            await usecase.get_portfolio_snapshots(user_id, address)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_portfolio_snapshots_exception_handling(
        self, wallet_usecase_with_di
    ):
        """Test get_portfolio_snapshots exception handling."""
        usecase = wallet_usecase_with_di
        user_id = uuid.uuid4()
        address = "0x1234567890123456789012345678901234567890"

        # Mock user exists
        user = Mock()
        user.id = user_id
        usecase._WalletUsecase__user_repo.get_by_id = AsyncMock(return_value=user)

        # Mock verify_wallet_ownership to raise exception
        usecase.verify_wallet_ownership = AsyncMock(
            side_effect=Exception("Database error")
        )

        # Execute and verify exception
        with pytest.raises(Exception, match="Database error"):
            await usecase.get_portfolio_snapshots(user_id, address)

        # Verify audit error was called
        usecase._WalletUsecase__audit.error.assert_called_once()
        error_call = usecase._WalletUsecase__audit.error.call_args
        assert error_call[0][0] == "wallet_usecase_get_portfolio_snapshots_failed"
        assert "Database error" in error_call[1]["error"]

    @pytest.mark.asyncio
    async def test_get_portfolio_metrics_user_not_found(self, wallet_usecase_with_di):
        """Test get_portfolio_metrics when user is not found."""
        usecase = wallet_usecase_with_di
        user_id = uuid.uuid4()
        address = "0x1234567890123456789012345678901234567890"

        # Mock user not found
        usecase._WalletUsecase__user_repo.get_by_id = AsyncMock(return_value=None)

        # Execute and verify exception
        with pytest.raises(HTTPException) as exc_info:
            await usecase.get_portfolio_metrics(user_id, address)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_portfolio_metrics_no_snapshots(self, wallet_usecase_with_di):
        """Test get_portfolio_metrics when no snapshots exist."""
        usecase = wallet_usecase_with_di
        user_id = uuid.uuid4()
        address = "0x1234567890123456789012345678901234567890"

        # Mock user exists
        user = Mock()
        user.id = user_id
        usecase._WalletUsecase__user_repo.get_by_id = AsyncMock(return_value=user)

        # Mock verify_wallet_ownership returns True
        usecase.verify_wallet_ownership = AsyncMock(return_value=True)

        # Mock empty snapshots
        usecase._WalletUsecase__portfolio_snapshot_repo.get_by_wallet_address = (
            AsyncMock(return_value=[])
        )

        # Execute
        with patch("app.usecase.wallet_usecase.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0, 0)
            result = await usecase.get_portfolio_metrics(user_id, address)

        # Verify empty metrics
        assert isinstance(result, PortfolioMetrics)
        assert result.user_address == address
        assert result.total_collateral == 0.0
        assert result.total_borrowings == 0.0
        assert result.total_collateral_usd == 0.0
        assert result.total_borrowings_usd == 0.0
        assert result.aggregate_health_score is None
        assert result.aggregate_apy is None
        assert result.collaterals == []
        assert result.borrowings == []
        assert result.staked_positions == []
        assert result.health_scores == []
        assert result.protocol_breakdown == {}

        # Verify audit warning was called
        usecase._WalletUsecase__audit.warning.assert_called_once()
        warning_call = usecase._WalletUsecase__audit.warning.call_args
        assert warning_call[0][0] == "wallet_usecase_get_portfolio_metrics_no_snapshots"

    @pytest.mark.asyncio
    async def test_get_portfolio_metrics_with_snapshots(self, wallet_usecase_with_di):
        """Test get_portfolio_metrics with existing snapshots."""
        usecase = wallet_usecase_with_di
        user_id = uuid.uuid4()
        address = "0x1234567890123456789012345678901234567890"

        # Mock user exists
        user = Mock()
        user.id = user_id
        usecase._WalletUsecase__user_repo.get_by_id = AsyncMock(return_value=user)

        # Mock verify_wallet_ownership returns True
        usecase.verify_wallet_ownership = AsyncMock(return_value=True)

        # Mock snapshots with data
        mock_snapshot = {
            "total_collateral": 1000.0,
            "total_borrowings": 500.0,
            "total_collateral_usd": 1500.0,
            "total_borrowings_usd": 750.0,
            "aggregate_health_score": 0.85,
            "aggregate_apy": 5.5,
            "collaterals": [],
            "borrowings": [],
            "staked_positions": [],
            "health_scores": [],
            "protocol_breakdown": {},
            "timestamp": datetime(2023, 1, 1, 12, 0, 0),
        }

        usecase._WalletUsecase__portfolio_snapshot_repo.get_by_wallet_address = (
            AsyncMock(return_value=[mock_snapshot])
        )

        # Execute
        result = await usecase.get_portfolio_metrics(user_id, address)

        # Verify metrics
        assert isinstance(result, PortfolioMetrics)
        assert result.user_address == address
        assert result.total_collateral == 1000.0
        assert result.total_borrowings == 500.0
        assert result.total_collateral_usd == 1500.0
        assert result.total_borrowings_usd == 750.0
        assert result.aggregate_health_score == 0.85
        assert result.aggregate_apy == 5.5
        assert result.collaterals == []
        assert result.borrowings == []
        assert result.staked_positions == []
        assert result.health_scores == []
        assert result.protocol_breakdown == {}

    @pytest.mark.asyncio
    async def test_get_portfolio_metrics_exception_handling(
        self, wallet_usecase_with_di
    ):
        """Test get_portfolio_metrics exception handling."""
        usecase = wallet_usecase_with_di
        user_id = uuid.uuid4()
        address = "0x1234567890123456789012345678901234567890"

        # Mock user exists
        user = Mock()
        user.id = user_id
        usecase._WalletUsecase__user_repo.get_by_id = AsyncMock(return_value=user)

        # Mock verify_wallet_ownership to raise exception
        usecase.verify_wallet_ownership = AsyncMock(
            side_effect=Exception("Database error")
        )

        # Execute and verify exception
        with pytest.raises(Exception, match="Database error"):
            await usecase.get_portfolio_metrics(user_id, address)

        # Verify audit error was called
        usecase._WalletUsecase__audit.error.assert_called_once()
        error_call = usecase._WalletUsecase__audit.error.call_args
        assert error_call[0][0] == "wallet_usecase_get_portfolio_metrics_failed"
        assert "Database error" in error_call[1]["error"]

    @pytest.mark.asyncio
    async def test_get_portfolio_timeline_user_not_found(self, wallet_usecase_with_di):
        """Test get_portfolio_timeline when user is not found."""
        usecase = wallet_usecase_with_di
        user_id = uuid.uuid4()
        address = "0x1234567890123456789012345678901234567890"

        # Mock user not found
        usecase._WalletUsecase__user_repo.get_by_id = AsyncMock(return_value=None)

        # Execute and verify exception
        with pytest.raises(HTTPException) as exc_info:
            await usecase.get_portfolio_timeline(user_id, address)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_portfolio_timeline_success(self, wallet_usecase_with_di):
        """Test get_portfolio_timeline success case."""
        usecase = wallet_usecase_with_di
        user_id = uuid.uuid4()
        address = "0x1234567890123456789012345678901234567890"

        # Mock user exists
        user = Mock()
        user.id = user_id
        usecase._WalletUsecase__user_repo.get_by_id = AsyncMock(return_value=user)

        # Mock verify_wallet_ownership returns True
        usecase.verify_wallet_ownership = AsyncMock(return_value=True)

        # Mock timeline data
        mock_timeline_data = [
            Mock(
                timestamp=1640995200,  # 2022-01-01 00:00:00
                total_collateral_usd=1000.0,
                total_borrowings_usd=500.0,
            ),
            Mock(
                timestamp=1641081600,  # 2022-01-02 00:00:00
                total_collateral_usd=1100.0,
                total_borrowings_usd=550.0,
            ),
        ]

        usecase._WalletUsecase__portfolio_snapshot_repo.get_timeline = AsyncMock(
            return_value=mock_timeline_data
        )

        # Execute
        with patch("app.usecase.wallet_usecase.datetime") as mock_datetime:
            mock_now = datetime(2023, 1, 1, 12, 0, 0)
            mock_datetime.now.return_value = mock_now
            result = await usecase.get_portfolio_timeline(user_id, address)

        # Verify timeline
        assert isinstance(result, PortfolioTimeline)
        assert result.timestamps == [1640995200, 1641081600]
        assert result.collateral_usd == [1000.0, 1100.0]
        assert result.borrowings_usd == [500.0, 550.0]

        # Verify portfolio snapshot repo was called with correct parameters
        usecase._WalletUsecase__portfolio_snapshot_repo.get_timeline.assert_called_once()
        call_args = (
            usecase._WalletUsecase__portfolio_snapshot_repo.get_timeline.call_args
        )
        assert call_args[0][0] == address  # user_address
        assert call_args[0][3] == 30  # limit
        assert call_args[0][4] == 0  # offset
        assert call_args[0][5] == "daily"  # interval

    @pytest.mark.asyncio
    async def test_get_portfolio_timeline_with_null_values(
        self, wallet_usecase_with_di
    ):
        """Test get_portfolio_timeline with null values in data."""
        usecase = wallet_usecase_with_di
        user_id = uuid.uuid4()
        address = "0x1234567890123456789012345678901234567890"

        # Mock user exists
        user = Mock()
        user.id = user_id
        usecase._WalletUsecase__user_repo.get_by_id = AsyncMock(return_value=user)

        # Mock verify_wallet_ownership returns True
        usecase.verify_wallet_ownership = AsyncMock(return_value=True)

        # Mock timeline data with null values
        mock_timeline_data = [
            Mock(
                timestamp=1640995200,
                total_collateral_usd=None,
                total_borrowings_usd=None,
            ),
        ]

        usecase._WalletUsecase__portfolio_snapshot_repo.get_timeline = AsyncMock(
            return_value=mock_timeline_data
        )

        # Execute
        with patch("app.usecase.wallet_usecase.datetime") as mock_datetime:
            mock_now = datetime(2023, 1, 1, 12, 0, 0)
            mock_datetime.now.return_value = mock_now
            result = await usecase.get_portfolio_timeline(user_id, address)

        # Verify timeline with null values converted to 0.0
        assert isinstance(result, PortfolioTimeline)
        assert result.timestamps == [1640995200]
        assert result.collateral_usd == [0.0]
        assert result.borrowings_usd == [0.0]

    @pytest.mark.asyncio
    async def test_get_portfolio_timeline_exception_handling(
        self, wallet_usecase_with_di
    ):
        """Test get_portfolio_timeline exception handling."""
        usecase = wallet_usecase_with_di
        user_id = uuid.uuid4()
        address = "0x1234567890123456789012345678901234567890"

        # Mock user exists
        user = Mock()
        user.id = user_id
        usecase._WalletUsecase__user_repo.get_by_id = AsyncMock(return_value=user)

        # Mock verify_wallet_ownership to raise exception
        usecase.verify_wallet_ownership = AsyncMock(
            side_effect=Exception("Database error")
        )

        # Execute and verify exception
        with pytest.raises(Exception, match="Database error"):
            await usecase.get_portfolio_timeline(user_id, address)

        # Verify audit error was called
        usecase._WalletUsecase__audit.error.assert_called_once()
        error_call = usecase._WalletUsecase__audit.error.call_args
        assert error_call[0][0] == "wallet_usecase_get_portfolio_timeline_failed"
        assert "Database error" in error_call[1]["error"]

    @pytest.mark.asyncio
    async def test_get_portfolio_timeline_custom_parameters(
        self, wallet_usecase_with_di
    ):
        """Test get_portfolio_timeline with custom parameters."""
        usecase = wallet_usecase_with_di
        user_id = uuid.uuid4()
        address = "0x1234567890123456789012345678901234567890"
        interval = "weekly"
        limit = 50
        offset = 10

        # Mock user exists
        user = Mock()
        user.id = user_id
        usecase._WalletUsecase__user_repo.get_by_id = AsyncMock(return_value=user)

        # Mock verify_wallet_ownership returns True
        usecase.verify_wallet_ownership = AsyncMock(return_value=True)

        # Mock timeline data
        usecase._WalletUsecase__portfolio_snapshot_repo.get_timeline = AsyncMock(
            return_value=[]
        )

        # Execute
        with patch("app.usecase.wallet_usecase.datetime") as mock_datetime:
            mock_now = datetime(2023, 1, 1, 12, 0, 0)
            mock_datetime.now.return_value = mock_now
            result = await usecase.get_portfolio_timeline(
                user_id, address, interval, limit, offset
            )

        # Verify portfolio snapshot repo was called with custom parameters
        usecase._WalletUsecase__portfolio_snapshot_repo.get_timeline.assert_called_once()
        call_args = (
            usecase._WalletUsecase__portfolio_snapshot_repo.get_timeline.call_args
        )
        assert call_args[0][0] == address  # user_address
        assert call_args[0][3] == limit  # limit
        assert call_args[0][4] == offset  # offset
        assert call_args[0][5] == interval  # interval
