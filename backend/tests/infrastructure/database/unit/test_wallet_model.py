import uuid

import pytest

from app.models.wallet import Wallet


def generate_unique_address():
    """Generate a unique Ethereum address for testing."""
    unique_hex = uuid.uuid4().hex + uuid.uuid4().hex
    return "0x" + unique_hex[:40]


@pytest.mark.asyncio
async def test_wallet_address_validation():
    """Test wallet address validation logic."""
    valid_wallet = Wallet(address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e")
    invalid_wallet = Wallet(address="invalid_address")
    assert valid_wallet.validate_address() is True
    assert invalid_wallet.validate_address() is False


def test_wallet_creation():
    """Test basic wallet model creation."""
    address = generate_unique_address()
    wallet = Wallet(address=address, name="Test Wallet")
    assert wallet.address == address
    assert wallet.name == "Test Wallet"


def test_wallet_default_values():
    """Test wallet model default values."""
    address = generate_unique_address()
    wallet = Wallet(address=address)
    assert wallet.address == address
    assert wallet.name is None  # Default should be None, not "Unnamed Wallet"
