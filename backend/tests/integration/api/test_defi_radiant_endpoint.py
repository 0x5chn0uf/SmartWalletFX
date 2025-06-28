from unittest.mock import AsyncMock, patch

import httpx
import pytest
from httpx import AsyncClient

from app.api.dependencies import blockchain_deps as deps
from app.main import app

TEST_ADDRESS = "0x1111111111111111111111111111111111111111"
TEST_ADDRESS_NOT_FOUND = "0x0000000000000000000000000000000000000000"


@pytest.mark.asyncio
@patch(
    "app.adapters.protocols.radiant.RadiantContractAdapter.async_get_user_data",
    new_callable=AsyncMock,
)
async def test_get_radiant_user_data_success(mock_async_get):
    """
    Test the /defi/radiant/{address} endpoint returns mapped
    user data for a valid address.
    """
    mock_async_get.return_value = {
        "reserves": [
            {
                "token_address": "0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                "symbol": "USDC",
                "decimals": 6,
                "supplied": 500_000_000,  # 500 USDC (6 decimals)
                "supplied_usd": 500.0,
                "used_as_collateral": True,
                "variable_borrowed": 0,
                "stable_borrowed": 0,
            },
            {
                "token_address": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
                "symbol": "ETH",
                "decimals": 18,
                "supplied": 0,
                "supplied_usd": 0.0,
                "used_as_collateral": False,
                "variable_borrowed": 100_000_000_000_000_000,  # 0.1 ETH
                "stable_borrowed": 0,
            },
        ],
        "health_factor": 2.5,
    }
    transport = httpx.ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/defi/radiant/0x000000000000000000000000000000000000dEaD")
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_address"] == "0x000000000000000000000000000000000000dEaD"
    assert len(data["collaterals"]) == 1
    assert (
        data["collaterals"][0]["asset"] == "0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    )
    assert data["collaterals"][0]["amount"] == 500.0
    assert data["collaterals"][0]["usd_value"] == 500.0
    assert len(data["borrowings"]) == 1
    assert (
        data["borrowings"][0]["asset"] == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
    )
    assert data["borrowings"][0]["amount"] == 0.1
    assert data["borrowings"][0]["usd_value"] == 0
    assert data["health_scores"][0]["score"] == 2.5


@pytest.mark.asyncio
@patch(
    "app.adapters.protocols.radiant.RadiantContractAdapter.async_get_user_data",
    new_callable=AsyncMock,
)
async def test_get_radiant_user_data_not_found(mock_async_get):
    """
    Test the /defi/radiant/{address} endpoint returns 404 if user not found.
    """
    mock_async_get.return_value = None
    transport = httpx.ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/defi/radiant/0x000000000000000000000000000000000000dead")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "User data not found on Radiant smart contract."


@pytest.mark.asyncio
async def test_radiant_user_endpoint(monkeypatch, test_app):
    """Radiant endpoint returns mocked snapshot and propagates JSON."""
    from app.schemas.defi import DeFiAccountSnapshot

    async def _mock_snapshot(address: str):  # noqa: D401
        return DeFiAccountSnapshot(
            user_address=address,
            timestamp=1234567890,
            collaterals=[],
            borrowings=[],
            staked_positions=[],
            health_scores=[],
            total_apy=0.0,
        )

    class MockRadiantUsecase:
        async def get_user_snapshot(self, address: str):
            return await _mock_snapshot(address)

    app.dependency_overrides[deps.get_radiant_usecase] = MockRadiantUsecase

    transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=True)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as ac:
        resp = await ac.get(f"/defi/radiant/{TEST_ADDRESS}")
    assert resp.status_code == 200
    assert resp.json()["user_address"].lower() == TEST_ADDRESS.lower()

    del app.dependency_overrides[deps.get_radiant_usecase]
