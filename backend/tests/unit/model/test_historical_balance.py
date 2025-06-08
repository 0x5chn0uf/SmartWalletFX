from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models import HistoricalBalance, Token, Wallet

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


def test_create_historical_balance(db_session):
    """Test creating historical balance records."""
    # Create wallet and token
    wallet = Wallet(address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e")
    token = Token(
        address="0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        symbol="WBTC",
        name="Wrapped Bitcoin",
    )
    db_session.add_all([wallet, token])
    db_session.commit()

    # Create historical balance
    timestamp = datetime.now(timezone.utc)
    hist_balance = HistoricalBalance(
        wallet_id=wallet.id,
        token_id=token.id,
        balance=100000000,
        balance_usd=20000.00,
        timestamp=timestamp,
    )
    db_session.add(hist_balance)
    db_session.commit()

    assert hist_balance.id is not None
    assert hist_balance.wallet.address == wallet.address
    assert hist_balance.token.symbol == "WBTC"
    assert hist_balance.timestamp.replace(tzinfo=timezone.utc) == timestamp
