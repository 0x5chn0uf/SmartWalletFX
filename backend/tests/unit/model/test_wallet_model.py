import pytest
from httpx import AsyncClient
from sqlalchemy import delete, select

from app.models.wallet import Wallet


@pytest.mark.parametrize(
    "address",
    [
        "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "0x742d35Cc6634C0532925a3b844Bc454e4438f44f",
    ],
)
@pytest.mark.asyncio
async def test_create_wallet(test_app, address):
    wallet_data = {"address": address, "name": "Test Wallet"}
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        resp = await ac.post("/wallets", json=wallet_data)
        assert resp.status_code == 201
        wallet = resp.json()
    assert wallet["id"] is not None
    assert wallet["address"] == address
    assert wallet["name"] == "Test Wallet"


@pytest.mark.asyncio
async def test_wallet_address_validation(db_session):
    valid_wallet = Wallet(address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e")
    invalid_wallet = Wallet(address="invalid_address")
    assert valid_wallet.validate_address() is True
    assert invalid_wallet.validate_address() is False


@pytest.mark.asyncio
async def test_wallet_default_name(test_app):
    address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        # Delete wallet if exists
        await ac.delete(f"/wallets/{address}")
        wallet_data = {"address": address}
        resp = await ac.post("/wallets", json=wallet_data)
        assert resp.status_code == 201
        wallet = resp.json()
    assert wallet["name"] == "Unnamed Wallet"
