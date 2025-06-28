"""
Unit tests for AggregateMetricsRepository implementation.

Tests the SQLAlchemy-based repository for aggregate metrics persistence.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.aggregate_metrics import AggregateMetricsModel
from app.repositories.aggregate_metrics_repository import (
    AggregateMetricsRepository,
)
from tests.fixtures import mock_async_session, sample_aggregate_metrics


class TestAggregateMetricsRepository:
    """Test cases for AggregateMetricsRepository."""

    @pytest.mark.asyncio
    async def test_repository_initialization(self, mock_async_session):
        """Test repository initialization with session."""
        repository = AggregateMetricsRepository(mock_async_session)
        assert repository._session == mock_async_session

    @pytest.mark.asyncio
    async def test_get_latest_success(
        self, mock_async_session, sample_aggregate_metrics
    ):
        """Test successful get_latest operation."""
        repository = AggregateMetricsRepository(mock_async_session)

        # Mock the execute result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_aggregate_metrics
        mock_async_session.execute.return_value = mock_result

        result = await repository.get_latest("0x1234567890abcdef")

        assert result == sample_aggregate_metrics
        mock_async_session.execute.assert_called_once()

        # Verify the query was constructed correctly
        call_args = mock_async_session.execute.call_args[0][0]
        assert "SELECT" in str(call_args)
        assert "aggregate_metrics" in str(call_args)
        assert "wallet_id" in str(call_args)
        assert "ORDER BY" in str(call_args)

    @pytest.mark.asyncio
    async def test_get_latest_no_results(self, mock_async_session):
        """Test get_latest when no results found."""
        repository = AggregateMetricsRepository(mock_async_session)

        # Mock the execute result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_async_session.execute.return_value = mock_result

        result = await repository.get_latest("0x1234567890abcdef")

        assert result is None
        mock_async_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_latest_lowercase_wallet_id(self, mock_async_session):
        """Test that wallet_id is converted to lowercase in get_latest."""
        repository = AggregateMetricsRepository(mock_async_session)

        # Mock the execute result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_async_session.execute.return_value = mock_result

        # Call with uppercase wallet_id - should be lowercased internally
        await repository.get_latest("0x1234567890ABCDEF")

        # Verify the method was called successfully
        mock_async_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_history_success(
        self, mock_async_session, sample_aggregate_metrics
    ):
        """Test successful get_history operation."""
        repository = AggregateMetricsRepository(mock_async_session)

        # Mock the execute result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_aggregate_metrics]
        mock_async_session.execute.return_value = mock_result

        result = await repository.get_history("0x1234567890abcdef", limit=10, offset=0)

        assert result == [sample_aggregate_metrics]
        mock_async_session.execute.assert_called_once()

        # Verify the query was constructed correctly
        call_args = mock_async_session.execute.call_args[0][0]
        assert "SELECT" in str(call_args)
        assert "aggregate_metrics" in str(call_args)
        assert "wallet_id" in str(call_args)
        assert "ORDER BY" in str(call_args)
        assert "LIMIT" in str(call_args)
        assert "OFFSET" in str(call_args)

    @pytest.mark.asyncio
    async def test_get_history_empty_results(self, mock_async_session):
        """Test get_history when no results found."""
        repository = AggregateMetricsRepository(mock_async_session)

        # Mock the execute result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_async_session.execute.return_value = mock_result

        result = await repository.get_history("0x1234567890abcdef")

        assert result == []
        mock_async_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_history_default_parameters(self, mock_async_session):
        """Test get_history with default parameters."""
        repository = AggregateMetricsRepository(mock_async_session)

        # Mock the execute result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_async_session.execute.return_value = mock_result

        await repository.get_history("0x1234567890abcdef")

        # Verify the method was called
        mock_async_session.execute.assert_called_once()

        # Verify the query structure (without checking parameterized values)
        call_args = mock_async_session.execute.call_args[0][0]
        query_str = str(call_args)
        assert "SELECT" in query_str
        assert "FROM aggregate_metrics" in query_str
        assert "ORDER BY aggregate_metrics.as_of DESC" in query_str
        assert "LIMIT" in query_str
        assert "OFFSET" in query_str

    @pytest.mark.asyncio
    async def test_get_history_lowercase_wallet_id(self, mock_async_session):
        """Test that wallet_id is converted to lowercase in get_history."""
        repository = AggregateMetricsRepository(mock_async_session)

        # Mock the execute result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_async_session.execute.return_value = mock_result

        # Call with uppercase wallet_id - should be lowercased internally
        await repository.get_history("0x1234567890ABCDEF")

        # Verify the method was called successfully
        mock_async_session.execute.assert_called_once()

        # Verify the wallet_id was lowercased in the query
        call_args = mock_async_session.execute.call_args[0][0]
        params = call_args.compile().params
        assert params["wallet_id_1"] == "0x1234567890abcdef"

    @pytest.mark.asyncio
    async def test_exists_true(self, mock_async_session):
        """Test exists when record exists."""
        repository = AggregateMetricsRepository(mock_async_session)

        # Mock the execute result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = 1
        mock_async_session.execute.return_value = mock_result

        result = await repository.exists("0x1234567890abcdef")

        assert result is True
        mock_async_session.execute.assert_called_once()
        call_args = mock_async_session.execute.call_args[0][0]
        assert "SELECT" in str(call_args)
        assert "FROM aggregate_metrics" in str(call_args)

    @pytest.mark.asyncio
    async def test_exists_false(self, mock_async_session):
        """Test exists when record does not exist."""
        repository = AggregateMetricsRepository(mock_async_session)

        # Mock the execute result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_async_session.execute.return_value = mock_result

        result = await repository.exists("0x1234567890abcdef")

        assert result is False
        mock_async_session.execute.assert_called_once()
        call_args = mock_async_session.execute.call_args[0][0]
        assert "SELECT" in str(call_args)
        assert "FROM aggregate_metrics" in str(call_args)

    @pytest.mark.asyncio
    async def test_exists_lowercase_wallet_id(self, mock_async_session):
        """Test that wallet_id is converted to lowercase in exists."""
        repository = AggregateMetricsRepository(mock_async_session)

        # Mock the execute result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_async_session.execute.return_value = mock_result

        # Call with uppercase wallet_id - should be lowercased internally
        await repository.exists("0x1234567890ABCDEF")

        # Verify the method was called successfully
        mock_async_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_success(self, mock_async_session, sample_aggregate_metrics):
        """Test successful save operation."""
        repository = AggregateMetricsRepository(mock_async_session)

        result = await repository.save(sample_aggregate_metrics)

        assert result == sample_aggregate_metrics
        mock_async_session.add.assert_called_once_with(sample_aggregate_metrics)
        mock_async_session.commit.assert_called_once()
        mock_async_session.refresh.assert_called_once_with(sample_aggregate_metrics)

    @pytest.mark.asyncio
    async def test_save_with_different_metrics(self, mock_async_session):
        """Test save with different metrics data."""
        repository = AggregateMetricsRepository(mock_async_session)

        metrics = AggregateMetricsModel(
            id=uuid4(),
            wallet_id="0xabcdef1234567890",
            tvl=2000.0,
            total_borrowings=500.0,
            aggregate_apy=0.12,
            as_of=datetime(2023, 6, 15, 18, 30, 0, tzinfo=timezone.utc),
            positions=[{"token": "USDC", "balance": 1000.0}],
        )

        result = await repository.save(metrics)

        assert result == metrics
        mock_async_session.add.assert_called_once_with(metrics)
        mock_async_session.commit.assert_called_once()
        mock_async_session.refresh.assert_called_once_with(metrics)

    @pytest.mark.asyncio
    async def test_upsert_create_new(
        self, mock_async_session, sample_aggregate_metrics
    ):
        """Test upsert when creating new record."""
        repository = AggregateMetricsRepository(mock_async_session)

        # Mock get_latest to return None (no existing record)
        with patch.object(repository, "get_latest", return_value=None):
            result = await repository.upsert(sample_aggregate_metrics)

            assert result == sample_aggregate_metrics
            mock_async_session.add.assert_called_once_with(sample_aggregate_metrics)
            mock_async_session.commit.assert_called_once()
            mock_async_session.refresh.assert_called_once_with(sample_aggregate_metrics)

    @pytest.mark.asyncio
    async def test_upsert_update_existing(
        self, mock_async_session, sample_aggregate_metrics
    ):
        """Test upsert when updating existing record."""
        repository = AggregateMetricsRepository(mock_async_session)

        # Create existing metrics
        existing_metrics = AggregateMetricsModel(
            id=uuid4(),
            wallet_id="0x1234567890abcdef",
            tvl=500.0,
            total_borrowings=100.0,
            aggregate_apy=0.05,
            as_of=datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            positions=[],
        )

        # Mock get_latest to return existing metrics
        with patch.object(repository, "get_latest", return_value=existing_metrics):
            # Mock the refresh method
            mock_async_session.refresh = AsyncMock()

            result = await repository.upsert(sample_aggregate_metrics)

            assert result == existing_metrics
            # Verify existing metrics were updated
            assert existing_metrics.tvl == sample_aggregate_metrics.tvl
            assert (
                existing_metrics.total_borrowings
                == sample_aggregate_metrics.total_borrowings
            )
            assert (
                existing_metrics.aggregate_apy == sample_aggregate_metrics.aggregate_apy
            )
            assert existing_metrics.positions == sample_aggregate_metrics.positions
            assert existing_metrics.as_of == sample_aggregate_metrics.as_of
            mock_async_session.commit.assert_called_once()
            mock_async_session.refresh.assert_called_once_with(existing_metrics)

    @pytest.mark.asyncio
    async def test_upsert_update_existing_with_none_apy(self, mock_async_session):
        """Test upsert when updating existing record with None APY."""
        repository = AggregateMetricsRepository(mock_async_session)

        # Create new metrics with None APY
        new_metrics = AggregateMetricsModel(
            id=uuid4(),
            wallet_id="0x1234567890abcdef",
            tvl=1500.0,
            total_borrowings=300.0,
            aggregate_apy=None,
            as_of=datetime(2023, 1, 1, 14, 0, 0, tzinfo=timezone.utc),
            positions=[{"token": "ETH", "balance": 5.0}],
        )

        # Create existing metrics
        existing_metrics = AggregateMetricsModel(
            id=uuid4(),
            wallet_id="0x1234567890abcdef",
            tvl=500.0,
            total_borrowings=100.0,
            aggregate_apy=0.05,
            as_of=datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            positions=[],
        )

        # Mock get_latest to return existing metrics
        with patch.object(repository, "get_latest", return_value=existing_metrics):
            # Mock the refresh method
            mock_async_session.refresh = AsyncMock()

            result = await repository.upsert(new_metrics)

            assert result == existing_metrics
            # Verify existing metrics were updated, including None APY
            assert existing_metrics.tvl == new_metrics.tvl
            assert existing_metrics.total_borrowings == new_metrics.total_borrowings
            assert existing_metrics.aggregate_apy is None
            assert existing_metrics.positions == new_metrics.positions
            assert existing_metrics.as_of == new_metrics.as_of

    @pytest.mark.asyncio
    async def test_delete_old_metrics_success(self, mock_async_session):
        """Test successful delete_old_metrics operation."""
        repository = AggregateMetricsRepository(mock_async_session)

        # Mock the execute result
        mock_result = MagicMock()
        mock_result.rowcount = 5
        mock_async_session.execute.return_value = mock_result

        before_date = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = await repository.delete_old_metrics("0x1234567890abcdef", before_date)

        assert result == 5
        mock_async_session.execute.assert_called_once()
        mock_async_session.commit.assert_called_once()

        # Verify the query was constructed correctly
        call_args = mock_async_session.execute.call_args[0][0]
        assert "DELETE" in str(call_args)
        assert "aggregate_metrics" in str(call_args)
        assert "wallet_id" in str(call_args)
        assert "as_of" in str(call_args)

    @pytest.mark.asyncio
    async def test_delete_old_metrics_no_deletions(self, mock_async_session):
        """Test delete_old_metrics when no records to delete."""
        repository = AggregateMetricsRepository(mock_async_session)

        # Mock the execute result
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_async_session.execute.return_value = mock_result

        before_date = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = await repository.delete_old_metrics("0x1234567890abcdef", before_date)

        assert result == 0
        mock_async_session.execute.assert_called_once()
        mock_async_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_old_metrics_lowercase_wallet_id(self, mock_async_session):
        """Test that wallet_id is converted to lowercase in delete_old_metrics."""
        repository = AggregateMetricsRepository(mock_async_session)

        # Mock the execute result
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_async_session.execute.return_value = mock_result

        before_date = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        await repository.delete_old_metrics("0x1234567890ABCDEF", before_date)

        # Verify the method was called successfully
        mock_async_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_old_metrics_with_different_date_formats(
        self, mock_async_session
    ):
        """Test delete_old_metrics with different date formats."""
        repository = AggregateMetricsRepository(mock_async_session)

        # Mock the execute result
        mock_result = MagicMock()
        mock_result.rowcount = 3
        mock_async_session.execute.return_value = mock_result

        # Test with different date formats
        dates = [
            datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            datetime(2023, 6, 15, 18, 30, 45, tzinfo=timezone.utc),
            datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        ]

        for before_date in dates:
            mock_async_session.execute.reset_mock()
            mock_async_session.commit.reset_mock()

            result = await repository.delete_old_metrics(
                "0x1234567890abcdef", before_date
            )

            assert result == 3
            mock_async_session.execute.assert_called_once()
            mock_async_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_repository_methods_with_empty_wallet_id(self, mock_async_session):
        """Test repository methods with empty wallet_id."""
        repository = AggregateMetricsRepository(mock_async_session)

        # Mock results
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_result.scalars.return_value.all.return_value = []
        mock_result.rowcount = 0
        mock_async_session.execute.return_value = mock_result
        mock_async_session.refresh = AsyncMock()

        # Test all methods with empty wallet_id
        await repository.get_latest("")
        await repository.get_history("")
        await repository.exists("")
        await repository.delete_old_metrics("", datetime.now(tz=timezone.utc))

        # Verify all calls were made
        assert mock_async_session.execute.call_count == 4

    @pytest.mark.asyncio
    async def test_repository_methods_with_special_characters_wallet_id(
        self, mock_async_session
    ):
        """Test repository methods with special characters in wallet_id."""
        repository = AggregateMetricsRepository(mock_async_session)

        # Mock results
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_result.scalars.return_value.all.return_value = []
        mock_result.rowcount = 0
        mock_async_session.execute.return_value = mock_result
        mock_async_session.refresh = AsyncMock()

        wallet_id = "0x1234567890abcdef!@#$%^&*()"

        # Test all methods with special characters
        await repository.get_latest(wallet_id)
        await repository.get_history(wallet_id)
        await repository.exists(wallet_id)
        await repository.delete_old_metrics(wallet_id, datetime.now(tz=timezone.utc))

        # Verify all calls were made
        assert mock_async_session.execute.call_count == 4

    @pytest.mark.asyncio
    async def test_save_with_session_errors(
        self, mock_async_session, sample_aggregate_metrics
    ):
        """Test save method when session operations fail."""
        repository = AggregateMetricsRepository(mock_async_session)

        # Mock session to raise exceptions
        mock_async_session.add.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await repository.save(sample_aggregate_metrics)

    @pytest.mark.asyncio
    async def test_upsert_with_session_errors(
        self, mock_async_session, sample_aggregate_metrics
    ):
        """Test upsert method when session operations fail."""
        repository = AggregateMetricsRepository(mock_async_session)

        # Mock get_latest to return None
        with patch.object(repository, "get_latest", return_value=None):
            # Mock session to raise exceptions
            mock_async_session.add.side_effect = Exception("Database error")

            with pytest.raises(Exception, match="Database error"):
                await repository.upsert(sample_aggregate_metrics)

    @pytest.mark.asyncio
    async def test_delete_old_metrics_with_session_errors(self, mock_async_session):
        """Test delete_old_metrics method when session operations fail."""
        repository = AggregateMetricsRepository(mock_async_session)

        # Mock session to raise exceptions
        mock_async_session.execute.side_effect = Exception("Database error")

        before_date = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        with pytest.raises(Exception, match="Database error"):
            await repository.delete_old_metrics("0x1234567890abcdef", before_date)
