import uuid

import pytest
from httpx import AsyncClient

from app.models import Token


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_token_model_directly(db_session):
    """Test token model creation directly without usecase layer."""
    # Generate a unique address each time to avoid conflicts
    unique_address = f"0x{uuid.uuid4().hex[:40]}"

    # Create token model directly
    token = Token(
        address=unique_address,
        symbol="TKN",
        name="Token",
        decimals=18,
    )

    # Add to session and commit
    db_session.add(token)
    await db_session.commit()
    await db_session.refresh(token)

    # Verify the result
    assert token.id is not None
    assert token.address == unique_address
    assert token.symbol == "TKN"
    assert token.name == "Token"
    assert token.decimals == 18


@pytest.mark.unit
@pytest.mark.asyncio
async def test_token_address_validation(db_session):
    valid_token = Token(
        address="0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        symbol="WBTC",
        name="Wrapped Bitcoin",
    )
    invalid_token = Token(
        address="invalid_address", symbol="WBTC", name="Wrapped Bitcoin"
    )
    assert valid_token.validate_address() is True
    assert invalid_token.validate_address() is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_token_symbol_validation(db_session):
    valid_token = Token(
        address="0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        symbol="WBTC",
        name="Wrapped Bitcoin",
    )
    invalid_token = Token(
        address="0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        symbol="wbtc",
        name="Wrapped Bitcoin",
    )
    assert valid_token.validate_symbol() is True
    assert invalid_token.validate_symbol() is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_token_decimals_validation(db_session):
    valid_token = Token(
        address="0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        symbol="WBTC",
        name="Wrapped Bitcoin",
        decimals=18,
    )
    invalid_token = Token(
        address="0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        symbol="WBTC",
        name="Wrapped Bitcoin",
        decimals=20,
    )
    assert valid_token.validate_decimals() is True
    assert invalid_token.validate_decimals() is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_token_price_validation(db_session):
    valid_token = Token(
        address="0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        symbol="WBTC",
        name="Wrapped Bitcoin",
        current_price_usd=20000.00,
    )
    invalid_token = Token(
        address="0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        symbol="WBTC",
        name="Wrapped Bitcoin",
        current_price_usd=-100.00,
    )
    assert valid_token.validate_price() is True
    assert invalid_token.validate_price() is False


# Add more tests for token validation and edge cases here.
