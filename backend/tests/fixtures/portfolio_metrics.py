"""Portfolio-related test fixtures."""

import datetime

import pytest

from app.usecase.portfolio_aggregation_usecase import PortfolioMetrics


@pytest.fixture()
def dummy_metrics():
    """Returns a dummy PortfolioMetrics object."""
    return PortfolioMetrics.model_construct(
        user_address="0xabc",
        total_collateral=1.0,
        total_borrowings=0.5,
        total_collateral_usd=1.0,
        total_borrowings_usd=0.5,
        aggregate_health_score=None,
        aggregate_apy=None,
        collaterals=[],
        borrowings=[],
        staked_positions=[],
        health_scores=[],
        protocol_breakdown={},
        historical_snapshots=None,
        timestamp=datetime.datetime.utcnow(),
    )
