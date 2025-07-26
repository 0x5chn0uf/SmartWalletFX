import uuid

import pytest

from app.models.wallet import Wallet

pytestmark = pytest.mark.integration


def generate_unique_address():
    """Generate a unique Ethereum address for testing."""
    unique_hex = uuid.uuid4().hex + uuid.uuid4().hex
    return "0x" + unique_hex[:40]


# @pytest.mark.skip(
#     reason="Event loop issue with authenticated_client fixture - needs investigation"
# )
@pytest.mark.asyncio
async def test_create_wallet(authenticated_client):
    """Test creating a wallet with unique address."""
    address = generate_unique_address()
    wallet_data = {"address": address, "name": "Test Wallet"}
    resp = await authenticated_client.post("/wallets", json=wallet_data)
    assert resp.status_code == 201
    wallet = resp.json()
    assert wallet["id"] is not None
    assert wallet["address"] == address
    assert wallet["name"] == "Test Wallet"


# @pytest.mark.skip(
#     reason="Event loop issue with authenticated_client fixture - needs investigation"
# )
@pytest.mark.asyncio
async def test_create_multiple_wallets(authenticated_client):
    """Test creating multiple wallets with unique addresses."""
    for i in range(2):
        address = generate_unique_address()
        wallet_data = {"address": address, "name": f"Test Wallet {i}"}
        resp = await authenticated_client.post("/wallets", json=wallet_data)
        assert resp.status_code == 201
        wallet = resp.json()
        assert wallet["address"] == address


# @pytest.mark.skip(
#     reason="Event loop issue with authenticated_client fixture - needs investigation"
# )
@pytest.mark.asyncio
async def test_wallet_default_name(authenticated_client):
    address = generate_unique_address()
    wallet_data = {"address": address}
    resp = await authenticated_client.post("/wallets", json=wallet_data)
    assert resp.status_code == 201
    wallet = resp.json()
    assert wallet["name"] == "Unnamed Wallet"
