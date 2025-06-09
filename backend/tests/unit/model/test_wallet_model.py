import pytest

from app.models import Wallet


def test_create_wallet(db_session):
    wallet = Wallet(
        address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        name="Test Wallet",
        balance=0.0
    )
    db_session.add(wallet)
    db_session.commit()
    assert wallet.id is not None
    assert wallet.address == "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    assert wallet.name == "Test Wallet"


def test_wallet_address_validation(db_session):
    valid_wallet = Wallet(address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e")
    invalid_wallet = Wallet(address="invalid_address")
    assert valid_wallet.validate_address() is True
    assert invalid_wallet.validate_address() is False


def test_wallet_default_name(db_session):
    wallet = Wallet(address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e", balance=0.0)
    db_session.add(wallet)
    db_session.commit()
    assert wallet.name == "Unnamed Wallet"
