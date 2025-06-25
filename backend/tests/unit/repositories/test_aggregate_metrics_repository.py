from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.aggregate_metrics import AggregateMetricsModel
from app.repositories.aggregate_metrics_repository import (
    AggregateMetricsRepository,
)


@pytest.fixture
def mock_db():
    return MagicMock()


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


def test_upsert_calls_db(repo, mock_db, sample_model):
    mock_db.merge = AsyncMock(return_value=sample_model)
    result = pytest.run(asyncio=True)(repo.upsert)(sample_model)
    assert result is not None
    mock_db.merge.assert_called_once()


def test_get_latest_calls_db(repo, mock_db):
    mock_db.query().filter().order_by().first = AsyncMock(return_value=None)
    result = pytest.run(asyncio=True)(repo.get_latest)(
        "0x1234567890abcdef1234567890abcdef12345678"
    )
    assert result is None
    mock_db.query().filter().order_by().first.assert_called_once()


def test_get_history_calls_db(repo, mock_db):
    mock_db.query().filter().order_by().offset().limit().all = AsyncMock(
        return_value=[]
    )
    result = pytest.run(asyncio=True)(repo.get_history)(
        "0x1234567890abcdef1234567890abcdef12345678", 10, 0
    )
    assert result == []
    mock_db.query().filter().order_by().offset().limit().all.assert_called_once()


def test_delete_old_metrics_calls_db(repo, mock_db):
    mock_db.query().filter().delete = AsyncMock(return_value=1)
    result = pytest.run(asyncio=True)(repo.delete_old_metrics)(
        "0x1234567890abcdef1234567890abcdef12345678", datetime.utcnow()
    )
    assert result == 1
    mock_db.query().filter().delete.assert_called_once()
