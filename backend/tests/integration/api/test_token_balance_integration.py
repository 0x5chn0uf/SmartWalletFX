import pytest
from httpx import AsyncClient


@pytest.mark.parametrize(
    "address",
    [
        "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C598",
    ],
)
@pytest.mark.asyncio
async def test_create_token_balance_integration(authenticated_client, address):
    """Integration test for creating token balances with authentication."""
    wallet_data = {
        "address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "name": "Test Wallet",
    }
    token_data = {
        "address": address,
        "symbol": "WBTC",
        "name": "Wrapped Bitcoin",
        "decimals": 18,
    }

    # Create wallet using authenticated client
    resp = await authenticated_client.post("/wallets", json=wallet_data)
    assert resp.status_code == 201
    wallet = resp.json()

    # Create token using authenticated client
    resp = await authenticated_client.post("/tokens", json=token_data)
    assert resp.status_code == 201
    token = resp.json()

    # Create token balance using authenticated client
    balance_data = {
        "token_id": token["id"],
        "wallet_id": wallet["id"],
        "balance": 1.23,
        "balance_usd": 20000.00,
    }
    resp = await authenticated_client.post("/token_balances", json=balance_data)
    assert resp.status_code == 201
    balance = resp.json()

    # Verify the created balance
    assert balance["id"] is not None
    assert float(balance["balance"]) == pytest.approx(1.23)
    assert float(balance["balance_usd"]) == 20000.00


@pytest.mark.asyncio
async def test_create_token_balance_unauthorized(test_app):
    """Test that creating token balances without authentication fails."""
    wallet_data = {
        "address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "name": "Test Wallet",
    }
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        # Try to create wallet without authentication
        resp = await ac.post("/wallets", json=wallet_data)
        assert resp.status_code == 401  # Should be unauthorized
