from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.aggregate_metrics import AggregateMetricsModel
from app.repositories.aggregate_metrics_repository import (
    AggregateMetricsRepository,
)


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def repo(mock_db):
    return AggregateMetricsRepository(mock_db)


@pytest.fixture
def sample_model():
    m = AggregateMetricsModel.create_new("0x1234567890abcdef1234567890abcdef12345678")
    m.id = "12345678-1234-5678-9abc-123456789abc"
    m.tvl = 1000.0
    m.total_borrowings = 200.0
    m.aggregate_apy = 0.05
    m.as_of = datetime.utcnow()
    m.positions = [
        {
            "protocol": "aave",
            "asset": "USDC",
            "amount": 1000.0,
            "usd_value": 1000.0,
            "apy": 0.05,
        }
    ]
    return m


@pytest.mark.asyncio
async def test_upsert_calls_db(repo, mock_db, sample_model):
    # Mock get_latest to return None (no existing record)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    # Mock add and commit for the save path
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    result = await repo.upsert(sample_model)
    assert result is not None
    mock_db.add.assert_called_once_with(sample_model)
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_get_latest_calls_db(repo, mock_db):
    # Patch execute to return a mock result with scalar_one_or_none() == None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)
    result = await repo.get_latest("0x1234567890abcdef1234567890abcdef12345678")
    assert result is None


@pytest.mark.asyncio
async def test_get_history_calls_db(repo, mock_db):
    # Patch execute to return a mock result with scalars().all() == []
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute = AsyncMock(return_value=mock_result)
    result = await repo.get_history("0x1234567890abcdef1234567890abcdef12345678", 10, 0)
    assert result == []


@pytest.mark.asyncio
async def test_delete_old_metrics_calls_db(repo, mock_db):
    # Patch execute to return a mock result with rowcount == 1
    mock_result = MagicMock()
    mock_result.rowcount = 1
    mock_db.execute = AsyncMock(return_value=mock_result)
    result = await repo.delete_old_metrics(
        "0x1234567890abcdef1234567890abcdef12345678", datetime.utcnow()
    )
    assert result == 1
