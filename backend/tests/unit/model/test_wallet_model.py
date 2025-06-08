import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base, engine
from app.main import app
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


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


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


def test_create_wallet_duplicate(client):
    addr = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    client.post("/wallets", json={"address": addr})
    response = client.post("/wallets", json={"address": addr})
    assert response.status_code == 400
    assert response.json()["detail"] == "Wallet address already exists."


def test_create_wallet_no_name(client):
    addr = "0x742d35Cc6634C0532925a3b844Bc454e4438f44f"
    response = client.post("/wallets", json={"address": addr})
    assert response.status_code == 201
    assert response.json()["name"] == "Unnamed Wallet"


def test_list_wallets_empty(client):
    response = client.get("/wallets")
    assert response.status_code == 200
    assert response.json() == []


def test_create_wallet_empty_name(client):
    addr = "0x742d35Cc6634C0532925a3b844Bc454e4438f450"
    response = client.post("/wallets", json={"address": addr, "name": ""})
    assert response.status_code == 201
    assert response.json()["name"] == ""


def test_create_wallet_long_name(client):
    addr = "0x742d35Cc6634C0532925a3b844Bc454e4438f451"
    long_name = "a" * 256
    response = client.post(
        "/wallets", json={"address": addr, "name": long_name}
    )
    assert response.status_code == 201
    assert response.json()["name"] == long_name


def test_create_wallet_mixed_case_address(client):
    addr = "0x742D35Cc6634C0532925A3b844Bc454e4438F452"
    response = client.post("/wallets", json={"address": addr})
    assert response.status_code == 201
    assert response.json()["address"] == addr


def test_wallet_balance_usd_default(client):
    addr = "0x742d35Cc6634C0532925a3b844Bc454e4438f453"
    response = client.post("/wallets", json={"address": addr})
    assert response.status_code == 201
    assert response.json()["balance_usd"] is None
