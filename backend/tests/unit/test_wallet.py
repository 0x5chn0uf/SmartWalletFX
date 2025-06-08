import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models import Wallet

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


def test_create_wallet(db_session):
    """Test creating a wallet with a valid EVM address."""
    wallet = Wallet(
        address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        name="Test Wallet",
    )
    db_session.add(wallet)
    db_session.commit()

    assert wallet.id is not None
    assert wallet.address == "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    assert wallet.name == "Test Wallet"


def test_wallet_address_validation(db_session):
    """Test wallet address validation."""
    valid_wallet = Wallet(address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e")
    invalid_wallet = Wallet(address="invalid_address")

    assert valid_wallet.validate_address() is True
    assert invalid_wallet.validate_address() is False


def test_wallet_default_name(db_session):
    """Test wallet default name assignment."""
    wallet = Wallet(address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e")
    db_session.add(wallet)
    db_session.commit()

    assert wallet.name == "Unnamed Wallet"


# Add more tests for different address types and validation logic here.
