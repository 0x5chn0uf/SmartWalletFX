from datetime import datetime, timezone

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_historical_balance(test_app, db_session):
    # Use the API to create the wallet
    wallet_data = {
        "address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "name": "Test Wallet",
    }
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        resp = await ac.post("/wallets", json=wallet_data)
        assert resp.status_code == 201
        wallet = resp.json()
        # Use the API to create the token
        token_data = {
            "address": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
            "symbol": "WBTC",
            "name": "Wrapped Bitcoin",
        }
        resp = await ac.post("/tokens", json=token_data)
        assert resp.status_code == 201
        token = resp.json()
        # Use the API to create the historical balance
        timestamp = datetime.now(timezone.utc).isoformat()
        hb_data = {
            "wallet_id": wallet["id"],
            "token_id": token["id"],
            "balance": 100.0,
            "balance_usd": 20000.00,
            "timestamp": timestamp,
        }
        resp = await ac.post("/historical_balances", json=hb_data)
        assert resp.status_code == 201
        hist_balance = resp.json()
    assert hist_balance["id"] is not None
    assert hist_balance["wallet_id"] == wallet["id"]
    assert hist_balance["token_id"] == token["id"]
    assert hist_balance["balance"] == 100.0
    assert hist_balance["timestamp"][:19] == timestamp[:19]
