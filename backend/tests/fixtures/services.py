"""
Service-specific test fixtures.

This module provides fixtures for testing service classes and their dependencies.
"""

from datetime import datetime

import pytest

from app.services.portfolio_service import PortfolioCalculationService

from .mocks import mock_db_session


@pytest.fixture
def portfolio_service(mock_db_session):
    """Portfolio calculation service instance."""
    return PortfolioCalculationService(mock_db_session)


@pytest.fixture
def mock_snapshot_data():
    """Mock portfolio snapshot data."""
    return {
        "user_address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "timestamp": int(datetime.utcnow().timestamp()),
        "total_collateral": 10.0,
        "total_borrowings": 2.0,
        "total_collateral_usd": 30000.0,
        "total_borrowings_usd": 2000.0,
        "aggregate_health_score": 0.85,
        "aggregate_apy": 0.08,
        "collaterals": [
            {
                "protocol": "AAVE",
                "asset": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                "amount": 1.5,
                "usd_value": 4500.0,
            },
            {
                "protocol": "COMPOUND",
                "asset": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
                "amount": 0.1,
                "usd_value": 4500.0,
            },
        ],
        "borrowings": [
            {
                "protocol": "AAVE",
                "asset": "0xA0b86a33E6441b8C4C8C8C8C8C8C8C8C8C8C8C8",
                "amount": 1000.0,
                "usd_value": 1000.0,
                "interest_rate": 0.05,
            },
            {
                "protocol": "COMPOUND",
                "asset": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
                "amount": 500.0,
                "usd_value": 500.0,
                "interest_rate": 0.03,
            },
        ],
        "staked_positions": [
            {
                "protocol": "AAVE",
                "asset": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
                "amount": 10.0,
                "usd_value": 1000.0,
                "apy": 0.08,
            }
        ],
        "health_scores": [
            {"protocol": "AAVE", "score": 0.85, "total_value": 5500.0},
            {"protocol": "COMPOUND", "score": 0.92, "total_value": 5000.0},
        ],
        "protocol_breakdown": {
            "AAVE": {
                "protocol": "AAVE",
                "total_collateral": 1.5,
                "total_borrowings": 1000.0,
                "aggregate_health_score": 0.85,
                "aggregate_apy": 0.08,
            },
            "COMPOUND": {
                "protocol": "COMPOUND",
                "total_collateral": 0.1,
                "total_borrowings": 500.0,
                "aggregate_health_score": 0.92,
                "aggregate_apy": 0.0,
            },
        },
    }
