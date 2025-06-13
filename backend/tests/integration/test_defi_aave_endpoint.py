import httpx
import pytest
import respx
from httpx import AsyncClient, Response

from app.main import app
from app.usecase.defi_aave_usecase import SUBGRAPH_URL

TEST_ADDRESS = "0x1111111111111111111111111111111111111111"
TEST_ADDRESS_NOT_FOUND = "0x0000000000000000000000000000000000000000"


@pytest.mark.asyncio
@respx.mock
async def test_get_aave_user_data_success():
    mock_response = {
        "data": {
            "userReserves": [
                {
                    "reserve": {
                        "symbol": "DAI",
                        "decimals": 18,
                        "liquidityRate": str(int(0.04 * 1e27)),
                        "variableBorrowRate": str(int(0.07 * 1e27)),
                    },
                    "scaledATokenBalance": str(int(1000 * 1e18)),
                    "currentTotalDebt": str(int(200 * 1e18)),
                }
            ],
            "userAccountData": {
                "healthFactor": str(int(2.1 * 1e18)),
                "totalCollateralETH": "10",
                "totalDebtETH": "2",
            },
        }
    }
    respx.post(SUBGRAPH_URL).mock(
        return_value=Response(200, json=mock_response)
    )
    transport = httpx.ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/defi/aave/0x123")
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_address"] == "0x123"
    assert len(data["collaterals"]) == 1
    assert data["collaterals"][0]["asset"] == "DAI"
    assert abs(data["collaterals"][0]["amount"] - 1000) < 1e-6
    assert len(data["borrowings"]) == 1
    assert data["borrowings"][0]["asset"] == "DAI"
    assert abs(data["borrowings"][0]["amount"] - 200) < 1e-6
    assert data["borrowings"][0]["interest_rate"] == 0.07
    assert len(data["staked_positions"]) == 1
    assert data["staked_positions"][0]["apy"] == 0.04
    assert len(data["health_scores"]) == 1
    assert abs(data["health_scores"][0]["score"] - 2.1) < 1e-6


@pytest.mark.asyncio
@respx.mock
async def test_get_aave_user_data_not_found():
    respx.post(SUBGRAPH_URL).mock(
        return_value=Response(
            200, json={"data": {"userReserves": [], "userAccountData": None}}
        )
    )
    transport = httpx.ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/defi/aave/0xdead")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "User data not found on Aave subgraph."


@pytest.mark.asyncio
async def test_aave_and_compound_endpoints(monkeypatch, test_app):
    """Aave and Compound endpoints propagate mocked snapshots."""
    from app.schemas.defi import DeFiAccountSnapshot

    async def _mock_snapshot(address: str):  # noqa: D401
        return DeFiAccountSnapshot(
            user_address=address,
            timestamp=123,
            collaterals=[],
            borrowings=[],
            staked_positions=[],
            health_scores=[],
            total_apy=None,
        )

    monkeypatch.setattr(
        "app.api.endpoints.defi.get_aave_user_snapshot_usecase",
        _mock_snapshot,
    )

    transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=True)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as ac:
        aave_resp = await ac.get(f"/defi/aave/{TEST_ADDRESS}")

    assert aave_resp.status_code == 200
