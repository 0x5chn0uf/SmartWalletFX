"""Unit tests for PortfolioSnapshotUsecase."""

import json
import uuid
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from app.domain.schemas.defi import PortfolioSnapshot
from app.models.portfolio_snapshot import (
    PortfolioSnapshot as PortfolioSnapshotModel,
)
from app.models.wallet import Wallet
from app.usecase.portfolio_snapshot_usecase import PortfolioSnapshotUsecase


class TestPortfolioSnapshotUsecase:
    """Test PortfolioSnapshotUsecase class."""

    @pytest.mark.unit
    def test_init(self, portfolio_snapshot_usecase_with_di):
        """Test PortfolioSnapshotUsecase initialization."""
        usecase = portfolio_snapshot_usecase_with_di

        assert usecase._PortfolioSnapshotUsecase__portfolio_snapshot_repo is not None
        assert usecase._PortfolioSnapshotUsecase__wallet_repo is not None
        assert usecase._PortfolioSnapshotUsecase__audit is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_snapshots_by_wallet_success(
        self, portfolio_snapshot_usecase_with_di
    ):
        """Test successful retrieval of portfolio snapshots by wallet."""
        usecase = portfolio_snapshot_usecase_with_di
        wallet_address = "0xabc123"
        user_id = uuid.uuid4()

        # Mock wallet exists
        wallet = Mock(spec=Wallet)
        wallet.id = user_id
        wallet.address = wallet_address

        # Mock portfolio snapshots
        mock_snapshots = [
            PortfolioSnapshotModel(
                user_address=wallet_address,
                timestamp=1000,
                total_collateral=50.0,
                total_borrowings=20.0,
                total_collateral_usd=100.0,
                total_borrowings_usd=40.0,
                aggregate_health_score=0.8,
                aggregate_apy=5.2,
                collaterals={},
                borrowings={},
                staked_positions={},
                health_scores={},
                protocol_breakdown={},
            ),
            PortfolioSnapshotModel(
                user_address=wallet_address,
                timestamp=2000,
                total_collateral=100.0,
                total_borrowings=30.0,
                total_collateral_usd=200.0,
                total_borrowings_usd=60.0,
                aggregate_health_score=0.9,
                aggregate_apy=6.5,
                collaterals={},
                borrowings={},
                staked_positions={},
                health_scores={},
                protocol_breakdown={},
            ),
        ]

        # Mock repository responses
        usecase._PortfolioSnapshotUsecase__wallet_repo.get_by_address = AsyncMock(
            return_value=wallet
        )
        usecase._PortfolioSnapshotUsecase__portfolio_snapshot_repo.get_by_wallet_address = AsyncMock(
            return_value=mock_snapshots
        )

        # Execute
        result = await usecase.get_snapshots_by_wallet(wallet_address)

        # Verify
        assert result == mock_snapshots
        usecase._PortfolioSnapshotUsecase__wallet_repo.get_by_address.assert_called_once_with(
            wallet_address
        )
        usecase._PortfolioSnapshotUsecase__portfolio_snapshot_repo.get_by_wallet_address.assert_called_once_with(
            wallet_address
        )

        # Verify audit logging
        usecase._PortfolioSnapshotUsecase__audit.info.assert_any_call(
            "portfolio_snapshot_usecase_get_by_wallet_started",
            wallet_address=wallet_address,
        )
        usecase._PortfolioSnapshotUsecase__audit.info.assert_any_call(
            "portfolio_snapshot_usecase_get_by_wallet_success",
            wallet_address=wallet_address,
            snapshot_count=len(mock_snapshots),
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_snapshots_by_wallet_not_found(
        self, portfolio_snapshot_usecase_with_di
    ):
        """Test get_snapshots_by_wallet when wallet is not found."""
        usecase = portfolio_snapshot_usecase_with_di
        wallet_address = "0xnotfound"

        # Mock wallet not found
        usecase._PortfolioSnapshotUsecase__wallet_repo.get_by_address = AsyncMock(
            return_value=None
        )

        # Execute and verify exception
        with pytest.raises(HTTPException) as exc_info:
            await usecase.get_snapshots_by_wallet(wallet_address)

        assert exc_info.value.status_code == 404
        assert "Wallet not found" in str(exc_info.value.detail)

        # Verify audit was called
        usecase._PortfolioSnapshotUsecase__audit.warning.assert_called_once_with(
            "portfolio_snapshot_usecase_wallet_not_found",
            wallet_address=wallet_address,
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_snapshots_by_wallet_empty_result(
        self, portfolio_snapshot_usecase_with_di
    ):
        """Test get_snapshots_by_wallet with empty result."""
        usecase = portfolio_snapshot_usecase_with_di
        wallet_address = "0xempty"

        # Mock wallet exists but no snapshots
        wallet = Mock(spec=Wallet)
        wallet.address = wallet_address

        usecase._PortfolioSnapshotUsecase__wallet_repo.get_by_address = AsyncMock(
            return_value=wallet
        )
        usecase._PortfolioSnapshotUsecase__portfolio_snapshot_repo.get_by_wallet_address = AsyncMock(
            return_value=[]
        )

        # Execute
        result = await usecase.get_snapshots_by_wallet(wallet_address)

        # Verify
        assert result == []

        # Verify audit logging
        usecase._PortfolioSnapshotUsecase__audit.info.assert_any_call(
            "portfolio_snapshot_usecase_get_by_wallet_success",
            wallet_address=wallet_address,
            snapshot_count=0,
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_snapshots_by_wallet_exception_handling(
        self, portfolio_snapshot_usecase_with_di
    ):
        """Test get_snapshots_by_wallet exception handling."""
        usecase = portfolio_snapshot_usecase_with_di
        wallet_address = "0xexception"

        # Mock exception
        usecase._PortfolioSnapshotUsecase__wallet_repo.get_by_address = AsyncMock(
            side_effect=Exception("Database error")
        )

        # Execute and verify exception
        with pytest.raises(Exception, match="Database error"):
            await usecase.get_snapshots_by_wallet(wallet_address)

        # Verify audit was called
        usecase._PortfolioSnapshotUsecase__audit.error.assert_called_once_with(
            "portfolio_snapshot_usecase_get_by_wallet_failed",
            wallet_address=wallet_address,
            error="Database error",
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_timeline_cache_hit(self, portfolio_snapshot_usecase_with_di):
        """Test get_timeline with cache hit."""
        usecase = portfolio_snapshot_usecase_with_di
        user_address = "0xuser123"
        from_ts = 1000
        to_ts = 2000
        limit = 100
        offset = 0
        interval = "daily"

        # Mock cache hit
        cached_data = [
            {
                "user_address": user_address,
                "timestamp": 1500,
                "total_collateral": 75.0,
                "total_borrowings": 25.0,
                "total_collateral_usd": 150.0,
                "total_borrowings_usd": 50.0,
                "aggregate_health_score": 0.85,
                "aggregate_apy": 5.8,
                "collaterals": [],
                "borrowings": [],
                "staked_positions": [],
                "health_scores": [],
                "protocol_breakdown": {},
            }
        ]

        usecase._PortfolioSnapshotUsecase__portfolio_snapshot_repo.get_cache = (
            AsyncMock(return_value=json.dumps(cached_data))
        )

        # Execute
        result = await usecase.get_timeline(
            user_address, from_ts, to_ts, limit, offset, interval
        )

        # Verify
        assert len(result) == 1
        assert isinstance(result[0], PortfolioSnapshot)
        assert result[0].user_address == user_address
        assert result[0].timestamp == 1500
        assert result[0].total_collateral == 75.0

        # Verify cache was called
        usecase._PortfolioSnapshotUsecase__portfolio_snapshot_repo.get_cache.assert_called_once_with(
            user_address, from_ts, to_ts, interval, limit, offset
        )

        # Verify audit logging
        usecase._PortfolioSnapshotUsecase__audit.info.assert_any_call(
            "portfolio_snapshot_usecase_get_timeline_cache_hit",
            user_address=user_address,
            snapshot_count=1,
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_timeline_cache_miss(self, portfolio_snapshot_usecase_with_di):
        """Test get_timeline with cache miss."""
        usecase = portfolio_snapshot_usecase_with_di
        user_address = "0xuser456"
        from_ts = 1000
        to_ts = 2000
        limit = 50
        offset = 10
        interval = "hourly"

        # Mock cache miss
        usecase._PortfolioSnapshotUsecase__portfolio_snapshot_repo.get_cache = (
            AsyncMock(return_value=None)
        )

        # Mock database result
        db_result = [
            Mock(
                user_address=user_address,
                timestamp=1200,
                total_collateral=60.0,
                total_borrowings=15.0,
                total_collateral_usd=120.0,
                total_borrowings_usd=30.0,
                aggregate_health_score=0.75,
                aggregate_apy=4.5,
                collaterals=[],
                borrowings=[],
                staked_positions=[],
                health_scores=[],
                protocol_breakdown={},
            ),
            Mock(
                user_address=user_address,
                timestamp=1800,
                total_collateral=80.0,
                total_borrowings=20.0,
                total_collateral_usd=160.0,
                total_borrowings_usd=40.0,
                aggregate_health_score=0.85,
                aggregate_apy=5.0,
                collaterals=[],
                borrowings=[],
                staked_positions=[],
                health_scores=[],
                protocol_breakdown={},
            ),
        ]

        usecase._PortfolioSnapshotUsecase__portfolio_snapshot_repo.get_timeline = (
            AsyncMock(return_value=db_result)
        )
        usecase._PortfolioSnapshotUsecase__portfolio_snapshot_repo.set_cache = (
            AsyncMock()
        )

        # Execute
        result = await usecase.get_timeline(
            user_address, from_ts, to_ts, limit, offset, interval
        )

        # Verify
        assert len(result) == 2
        assert all(isinstance(r, PortfolioSnapshot) for r in result)
        assert result[0].user_address == user_address
        assert result[0].timestamp == 1200
        assert result[1].timestamp == 1800

        # Verify database was called
        usecase._PortfolioSnapshotUsecase__portfolio_snapshot_repo.get_timeline.assert_called_once_with(
            user_address, from_ts, to_ts, limit, offset, interval
        )

        # Verify cache was set
        usecase._PortfolioSnapshotUsecase__portfolio_snapshot_repo.set_cache.assert_called_once()
        cache_call_args = usecase._PortfolioSnapshotUsecase__portfolio_snapshot_repo.set_cache.call_args[
            1
        ]
        assert cache_call_args["user_address"] == user_address
        assert cache_call_args["from_ts"] == from_ts
        assert cache_call_args["to_ts"] == to_ts
        assert cache_call_args["interval"] == interval
        assert cache_call_args["limit"] == limit
        assert cache_call_args["offset"] == offset

        # Verify audit logging
        usecase._PortfolioSnapshotUsecase__audit.info.assert_any_call(
            "portfolio_snapshot_usecase_get_timeline_success",
            user_address=user_address,
            snapshot_count=2,
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_timeline_default_parameters(
        self, portfolio_snapshot_usecase_with_di
    ):
        """Test get_timeline with default parameters."""
        usecase = portfolio_snapshot_usecase_with_di
        user_address = "0xdefault"
        from_ts = 1000
        to_ts = 2000

        # Mock cache miss and empty result
        usecase._PortfolioSnapshotUsecase__portfolio_snapshot_repo.get_cache = (
            AsyncMock(return_value=None)
        )
        usecase._PortfolioSnapshotUsecase__portfolio_snapshot_repo.get_timeline = (
            AsyncMock(return_value=[])
        )
        usecase._PortfolioSnapshotUsecase__portfolio_snapshot_repo.set_cache = (
            AsyncMock()
        )

        # Execute with default parameters
        result = await usecase.get_timeline(user_address, from_ts, to_ts)

        # Verify default parameters were used
        usecase._PortfolioSnapshotUsecase__portfolio_snapshot_repo.get_timeline.assert_called_once_with(
            user_address, from_ts, to_ts, 100, 0, "none"  # default values
        )

        assert result == []

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_timeline_exception_handling(
        self, portfolio_snapshot_usecase_with_di
    ):
        """Test get_timeline exception handling."""
        usecase = portfolio_snapshot_usecase_with_di
        user_address = "0xerror"
        from_ts = 1000
        to_ts = 2000

        # Mock exception
        usecase._PortfolioSnapshotUsecase__portfolio_snapshot_repo.get_cache = (
            AsyncMock(side_effect=Exception("Cache error"))
        )

        # Execute and verify exception
        with pytest.raises(Exception, match="Cache error"):
            await usecase.get_timeline(user_address, from_ts, to_ts)

        # Verify audit was called
        usecase._PortfolioSnapshotUsecase__audit.error.assert_called_once_with(
            "portfolio_snapshot_usecase_get_timeline_failed",
            user_address=user_address,
            error="Cache error",
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_timeline_json_serialization(
        self, portfolio_snapshot_usecase_with_di
    ):
        """Test get_timeline JSON serialization for caching."""
        usecase = portfolio_snapshot_usecase_with_di
        user_address = "0xjson"
        from_ts = 1000
        to_ts = 2000

        # Mock cache miss
        usecase._PortfolioSnapshotUsecase__portfolio_snapshot_repo.get_cache = (
            AsyncMock(return_value=None)
        )

        # Mock database result with complex data
        db_result = [
            Mock(
                user_address=user_address,
                timestamp=1500,
                total_collateral=100.0,
                total_borrowings=50.0,
                total_collateral_usd=200.0,
                total_borrowings_usd=100.0,
                aggregate_health_score=0.9,
                aggregate_apy=6.0,
                collaterals=[],
                borrowings=[],
                staked_positions=[],
                health_scores=[],
                protocol_breakdown={
                    "aave": {"collateral": 50.0},
                    "compound": {"collateral": 50.0},
                },
            ),
        ]

        usecase._PortfolioSnapshotUsecase__portfolio_snapshot_repo.get_timeline = (
            AsyncMock(return_value=db_result)
        )
        usecase._PortfolioSnapshotUsecase__portfolio_snapshot_repo.set_cache = (
            AsyncMock()
        )

        # Execute
        result = await usecase.get_timeline(user_address, from_ts, to_ts)

        # Verify result
        assert len(result) == 1
        assert result[0].protocol_breakdown == {
            "aave": {"collateral": 50.0},
            "compound": {"collateral": 50.0},
        }

        # Verify cache was set with JSON string
        usecase._PortfolioSnapshotUsecase__portfolio_snapshot_repo.set_cache.assert_called_once()
        cache_call_args = usecase._PortfolioSnapshotUsecase__portfolio_snapshot_repo.set_cache.call_args[
            1
        ]
        response_json = cache_call_args["response_json"]

        # Verify JSON can be parsed
        parsed_json = json.loads(response_json)
        assert len(parsed_json) == 1
        assert parsed_json[0]["user_address"] == user_address
        assert parsed_json[0]["protocol_breakdown"] == {
            "aave": {"collateral": 50.0},
            "compound": {"collateral": 50.0},
        }

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_timeline_with_all_parameters(
        self, portfolio_snapshot_usecase_with_di
    ):
        """Test get_timeline with all parameters specified."""
        usecase = portfolio_snapshot_usecase_with_di
        user_address = "0xfull"
        from_ts = 1000
        to_ts = 2000
        limit = 25
        offset = 5
        interval = "weekly"

        # Mock cache miss and empty result
        usecase._PortfolioSnapshotUsecase__portfolio_snapshot_repo.get_cache = (
            AsyncMock(return_value=None)
        )
        usecase._PortfolioSnapshotUsecase__portfolio_snapshot_repo.get_timeline = (
            AsyncMock(return_value=[])
        )
        usecase._PortfolioSnapshotUsecase__portfolio_snapshot_repo.set_cache = (
            AsyncMock()
        )

        # Execute with all parameters
        result = await usecase.get_timeline(
            user_address, from_ts, to_ts, limit, offset, interval
        )

        # Verify all parameters were passed correctly
        usecase._PortfolioSnapshotUsecase__portfolio_snapshot_repo.get_cache.assert_called_once_with(
            user_address, from_ts, to_ts, interval, limit, offset
        )
        usecase._PortfolioSnapshotUsecase__portfolio_snapshot_repo.get_timeline.assert_called_once_with(
            user_address, from_ts, to_ts, limit, offset, interval
        )

        # Verify audit logging includes all parameters
        usecase._PortfolioSnapshotUsecase__audit.info.assert_any_call(
            "portfolio_snapshot_usecase_get_timeline_started",
            user_address=user_address,
            from_ts=from_ts,
            to_ts=to_ts,
            interval=interval,
            limit=limit,
            offset=offset,
        )

        assert result == []

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_timeline_invalid_cached_json(
        self, portfolio_snapshot_usecase_with_di
    ):
        """Test get_timeline with invalid JSON in cache."""
        usecase = portfolio_snapshot_usecase_with_di
        user_address = "0xinvalid"
        from_ts = 1000
        to_ts = 2000

        # Mock cache with invalid JSON
        usecase._PortfolioSnapshotUsecase__portfolio_snapshot_repo.get_cache = (
            AsyncMock(return_value="invalid json")
        )

        # Execute and verify exception
        with pytest.raises(Exception):  # JSON decode error
            await usecase.get_timeline(user_address, from_ts, to_ts)

        # Verify audit was called
        usecase._PortfolioSnapshotUsecase__audit.error.assert_called_once()
        error_call = usecase._PortfolioSnapshotUsecase__audit.error.call_args[0]
        assert error_call[0] == "portfolio_snapshot_usecase_get_timeline_failed"
