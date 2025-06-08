from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models import Token, TokenPrice

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


def test_create_token_price(db_session):
    """Test creating token price records."""
    # Create token
    token = Token(
        address="0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        symbol="WBTC",
        name="Wrapped Bitcoin",
    )
    db_session.add(token)
    db_session.commit()

    # Create token price
    timestamp = datetime.now(timezone.utc)
    price = TokenPrice(
        token_id=token.id, price_usd=20000.00, timestamp=timestamp
    )
    db_session.add(price)
    db_session.commit()

    assert price.id is not None
    assert price.token.symbol == "WBTC"
    assert float(price.price_usd) == 20000.00
    assert price.timestamp.replace(tzinfo=timezone.utc) == timestamp


# Add more tests for token price validation and edge cases here.
