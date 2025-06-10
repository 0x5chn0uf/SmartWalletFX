import pytest
import respx
from httpx import AsyncClient, Response

from app.main import app
from app.usecase.defi_compound_usecase import SUBGRAPH_URL


@pytest.mark.asyncio
@respx.mock
async def test_get_compound_user_data_success():
    mock_response = {
        "data": {
            "account": {
                "id": "0x123",
                "health": "1.8",
                "tokens": [
                    {
                        "symbol": "USDC",
                        "supplyBalanceUnderlying": "500",
                        "borrowBalanceUnderlying": "0",
                    },
                    {
                        "symbol": "ETH",
                        "supplyBalanceUnderlying": "0",
                        "borrowBalanceUnderlying": "0.5",
                    },
                ],
            }
        }
    }
    respx.post(SUBGRAPH_URL).mock(
        return_value=Response(200, json=mock_response)
    )
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/defi/compound/0x123")
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_address"] == "0x123"
    assert len(data["collaterals"]) == 1
    assert data["collaterals"][0]["asset"] == "USDC"
    assert abs(data["collaterals"][0]["amount"] - 500) < 1e-6
    assert len(data["borrowings"]) == 1
    assert data["borrowings"][0]["asset"] == "ETH"
    assert abs(data["borrowings"][0]["amount"] - 0.5) < 1e-6
    assert len(data["health_scores"]) == 1
    assert abs(data["health_scores"][0]["score"] - 1.8) < 1e-6


@pytest.mark.asyncio
@respx.mock
async def test_get_compound_user_data_not_found():
    respx.post(SUBGRAPH_URL).mock(
        return_value=Response(200, json={"data": {"account": None}})
    )
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/defi/compound/0xdead")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "User data not found on Compound subgraph."
