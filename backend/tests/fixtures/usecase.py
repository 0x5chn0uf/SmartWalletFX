"""
Usecase-specific test fixtures.

This module provides fixtures for testing usecase classes and their dependencies.
"""

import uuid
from datetime import datetime

import pytest

from app.usecase.historical_balance_usecase import HistoricalBalanceUsecase

from .mocks import mock_db_session


@pytest.fixture
def historical_balance_usecase(mock_db_session):
    """Historical balance usecase instance."""
    return HistoricalBalanceUsecase(mock_db_session)


@pytest.fixture
def sample_historical_balance_data():
    """Sample data for historical balance creation."""
    return {
        "wallet_id": uuid.uuid4(),
        "token_id": uuid.uuid4(),
        "balance": 100.5,
        "balance_usd": 150.75,
        "timestamp": datetime.utcnow(),
    }
