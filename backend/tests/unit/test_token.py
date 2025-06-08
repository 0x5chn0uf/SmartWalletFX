import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models import Token

# Test database URL
TEST_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine(
        TEST_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(bind=engine)


def test_create_token(db_session):
    """Test creating a token."""
    token = Token(
        address="0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        symbol="WBTC",
        name="Wrapped Bitcoin",
        decimals=8,
    )
    db_session.add(token)
    db_session.commit()

    assert token.id is not None
    assert token.symbol == "WBTC"
    assert token.decimals == 8


def test_token_address_validation(db_session):
    """Test token address validation."""
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


def test_token_symbol_validation(db_session):
    """Test token symbol validation."""
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


def test_token_decimals_validation(db_session):
    """Test token decimals validation."""
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


def test_token_price_validation(db_session):
    """Test token price validation."""
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
