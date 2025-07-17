"""
Unit tests for HistoricalBalanceUsecase.

Tests the historical balance operations including creation and management.
"""

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from app.domain.schemas.historical_balance import (
    HistoricalBalanceCreate,
    HistoricalBalanceResponse,
)


@pytest.fixture
def sample_historical_balance_data():
    """Sample historical balance data for testing."""
    return {
        "wallet_id": uuid.uuid4(),
        "token_id": uuid.uuid4(),
        "balance": 100.0,
        "balance_usd": 150.0,
        "timestamp": datetime.utcnow(),
    }


@pytest.fixture
def historical_balance_usecase(historical_balance_usecase_with_di):
    """Alias fixture for consistency with test expectations."""
    return historical_balance_usecase_with_di


class TestHistoricalBalanceUsecase:
    """Test cases for HistoricalBalanceUsecase."""

    @pytest.mark.asyncio
    async def test_create_historical_balance_success(
        self, historical_balance_usecase, sample_historical_balance_data
    ):
        """Test successful historical balance creation."""
        # Mock repository response
        mock_response = HistoricalBalanceResponse(
            id=uuid.uuid4(), **sample_historical_balance_data
        )
        historical_balance_usecase._HistoricalBalanceUsecase__historical_balance_repo.create = AsyncMock(
            return_value=mock_response
        )

        # Create historical balance
        hb_create = HistoricalBalanceCreate(**sample_historical_balance_data)
        result = await historical_balance_usecase.create_historical_balance(hb_create)

        # Verify result
        assert result == mock_response
        assert result.id == mock_response.id
        assert result.wallet_id == sample_historical_balance_data["wallet_id"]
        assert result.token_id == sample_historical_balance_data["token_id"]
        assert result.balance == sample_historical_balance_data["balance"]
        assert result.balance_usd == sample_historical_balance_data["balance_usd"]
        assert result.timestamp == sample_historical_balance_data["timestamp"]

        # Verify repository was called
        historical_balance_usecase._HistoricalBalanceUsecase__historical_balance_repo.create.assert_called_once_with(
            hb_create
        )

    @pytest.mark.asyncio
    async def test_create_historical_balance_with_minimal_data(
        self, historical_balance_usecase
    ):
        """Test historical balance creation with minimal required data."""
        minimal_data = {
            "wallet_id": uuid.uuid4(),
            "token_id": uuid.uuid4(),
            "balance": 50.0,
            "balance_usd": 75.0,
            "timestamp": datetime.utcnow(),
        }

        mock_response = HistoricalBalanceResponse(
            id=uuid.uuid4(),
            **minimal_data,
        )
        historical_balance_usecase._HistoricalBalanceUsecase__historical_balance_repo.create = AsyncMock(
            return_value=mock_response
        )

        hb_create = HistoricalBalanceCreate(**minimal_data)
        result = await historical_balance_usecase.create_historical_balance(hb_create)

        assert result == mock_response
        assert result.id == mock_response.id
        assert result.wallet_id == minimal_data["wallet_id"]
        assert result.token_id == minimal_data["token_id"]
        assert result.balance == minimal_data["balance"]
        assert result.balance_usd == minimal_data["balance_usd"]
        assert result.timestamp == minimal_data["timestamp"]

    @pytest.mark.asyncio
    async def test_create_historical_balance_with_zero_values(
        self, historical_balance_usecase
    ):
        """Test historical balance creation with zero values."""
        zero_data = {
            "wallet_id": uuid.uuid4(),
            "token_id": uuid.uuid4(),
            "balance": 0.0,
            "balance_usd": 0.0,
            "timestamp": datetime.utcnow(),
        }

        mock_response = HistoricalBalanceResponse(id=uuid.uuid4(), **zero_data)
        historical_balance_usecase._HistoricalBalanceUsecase__historical_balance_repo.create = AsyncMock(
            return_value=mock_response
        )

        hb_create = HistoricalBalanceCreate(**zero_data)
        result = await historical_balance_usecase.create_historical_balance(hb_create)

        assert result == mock_response
        assert result.balance == 0.0
        assert result.balance_usd == 0.0

    @pytest.mark.asyncio
    async def test_create_historical_balance_with_large_values(
        self, historical_balance_usecase
    ):
        """Test historical balance creation with large values."""
        large_data = {
            "wallet_id": uuid.uuid4(),
            "token_id": uuid.uuid4(),
            "balance": 999999999.999999,
            "balance_usd": 999999999999.99,
            "timestamp": datetime.utcnow(),
        }

        mock_response = HistoricalBalanceResponse(id=uuid.uuid4(), **large_data)
        historical_balance_usecase._HistoricalBalanceUsecase__historical_balance_repo.create = AsyncMock(
            return_value=mock_response
        )

        hb_create = HistoricalBalanceCreate(**large_data)
        result = await historical_balance_usecase.create_historical_balance(hb_create)

        assert result == mock_response
        assert result.balance == 999999999.999999
        assert result.balance_usd == 999999999999.99
        assert result.timestamp == large_data["timestamp"]

    @pytest.mark.asyncio
    async def test_create_historical_balance_repository_error(
        self, historical_balance_usecase, sample_historical_balance_data
    ):
        """Test historical balance creation when repository raises an error."""
        historical_balance_usecase._HistoricalBalanceUsecase__historical_balance_repo.create = AsyncMock(
            side_effect=Exception("Database error")
        )

        hb_create = HistoricalBalanceCreate(**sample_historical_balance_data)

        with pytest.raises(Exception, match="Database error"):
            await historical_balance_usecase.create_historical_balance(hb_create)

        historical_balance_usecase._HistoricalBalanceUsecase__historical_balance_repo.create.assert_called_once_with(
            hb_create
        )

    @pytest.mark.asyncio
    async def test_create_historical_balance_validation_error(
        self, historical_balance_usecase
    ):
        """Test historical balance creation with invalid data types."""
        from pydantic import ValidationError

        # Test with invalid UUID type
        invalid_data = {
            "wallet_id": "not-a-uuid",  # Invalid UUID format
            "token_id": uuid.uuid4(),
            "balance": 100.0,
            "balance_usd": 150.0,
            "timestamp": datetime.utcnow(),
        }

        with pytest.raises(ValidationError):  # Should raise validation error
            HistoricalBalanceCreate(**invalid_data)

    @pytest.mark.asyncio
    async def test_create_historical_balance_multiple_protocols(
        self, historical_balance_usecase
    ):
        """Test historical balance creation for different protocols."""
        protocols = ["AAVE", "COMPOUND", "RADIANT", "MAKER", "UNISWAP"]

        for i, protocol in enumerate(protocols):
            data = {
                "wallet_id": uuid.uuid4(),
                "token_id": uuid.uuid4(),
                "balance": 100.0 + i,
                "balance_usd": 150.0 + (i * 100.0),
                "timestamp": datetime.utcnow(),
            }

            mock_response = HistoricalBalanceResponse(id=uuid.uuid4(), **data)
            historical_balance_usecase._HistoricalBalanceUsecase__historical_balance_repo.create = AsyncMock(
                return_value=mock_response
            )

            hb_create = HistoricalBalanceCreate(**data)
            result = await historical_balance_usecase.create_historical_balance(
                hb_create
            )

            assert result == mock_response
            assert result.balance == 100.0 + i
            assert result.balance_usd == 150.0 + (i * 100.0)

    @pytest.mark.asyncio
    async def test_create_historical_balance_edge_case_timestamps(
        self, historical_balance_usecase
    ):
        """Test historical balance creation with edge case timestamps."""
        edge_timestamps = [0, 1, 9999999999, datetime.utcnow().timestamp()]

        for i, timestamp in enumerate(edge_timestamps):
            data = {
                "wallet_id": uuid.uuid4(),
                "token_id": uuid.uuid4(),
                "balance": 100.0,
                "balance_usd": 150.0,
                "timestamp": datetime.fromtimestamp(timestamp),
            }

            mock_response = HistoricalBalanceResponse(id=uuid.uuid4(), **data)
            historical_balance_usecase._HistoricalBalanceUsecase__historical_balance_repo.create = AsyncMock(
                return_value=mock_response
            )

            hb_create = HistoricalBalanceCreate(**data)
            result = await historical_balance_usecase.create_historical_balance(
                hb_create
            )

            assert result == mock_response
            assert result.timestamp == data["timestamp"]

    @pytest.mark.asyncio
    async def test_create_historical_balance_concurrent_creation(
        self, historical_balance_usecase, sample_historical_balance_data
    ):
        """Test concurrent historical balance creation."""
        import asyncio

        # Create multiple historical balances concurrently
        async def create_balance(i):
            data = sample_historical_balance_data.copy()
            data["timestamp"] = data["timestamp"] + timedelta(seconds=i)
            data["balance"] += i

            mock_response = HistoricalBalanceResponse(id=uuid.uuid4(), **data)
            historical_balance_usecase._HistoricalBalanceUsecase__historical_balance_repo.create = AsyncMock(
                return_value=mock_response
            )

            hb_create = HistoricalBalanceCreate(**data)
            return await historical_balance_usecase.create_historical_balance(hb_create)

        # Create 5 balances concurrently
        tasks = [create_balance(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        for i, result in enumerate(results):
            assert isinstance(result, HistoricalBalanceResponse)
            assert result.timestamp == sample_historical_balance_data[
                "timestamp"
            ] + timedelta(seconds=i)
            assert result.balance == sample_historical_balance_data["balance"] + i
