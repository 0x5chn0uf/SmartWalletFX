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
async def test_create_token_price(test_app, address):
    token_data = {
        "address": address,
        "symbol": "TKN",
        "name": "Token",
        "decimals": 18,
    }
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        resp = await ac.post("/tokens", json=token_data)
        assert resp.status_code == 201
        token = resp.json()
        price_data = {"token_id": token["id"], "price_usd": 123.45}
        resp = await ac.post("/token_prices", json=price_data)
        assert resp.status_code == 201
        price = resp.json()
    assert price["id"] is not None


# Add more tests for token price validation and edge cases here.
