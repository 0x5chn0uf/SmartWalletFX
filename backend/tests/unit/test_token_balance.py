import pytest
from app.core.database import Base
from app.models import Token, TokenBalance, Wallet
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Test database URL
TEST_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(bind=engine)


def test_create_token_balance(db_session):
    """Test creating a token balance for a wallet."""
    # Create wallet and token first
    wallet = Wallet(address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e")
    token = Token(
        address="0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        symbol="WBTC",
        name="Wrapped Bitcoin",
    )
    db_session.add_all([wallet, token])
    db_session.commit()

    # Create token balance
    balance = TokenBalance(
        wallet_id=wallet.id,
        token_id=token.id,
        balance=100000000,  # 1 WBTC
        balance_usd=20000.00,
    )
    db_session.add(balance)
    db_session.commit()

    assert balance.id is not None
    assert balance.wallet.address == wallet.address
    assert balance.token.symbol == "WBTC"
    assert float(balance.balance) == 100000000
    assert float(balance.balance_usd) == 20000.00


# Add more tests for balance validation and edge cases here.
