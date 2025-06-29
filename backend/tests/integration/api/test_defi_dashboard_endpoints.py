import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_get_defi_kpi():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/defi/portfolio/kpi")
    assert resp.status_code == 200
    data = resp.json()
    assert "tvl" in data
    assert "apy" in data
    assert "protocols" in data
    assert isinstance(data["protocols"], list)
    assert data["protocols"][0]["name"] == "Aave"


@pytest.mark.asyncio
async def test_get_protocol_breakdown():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/defi/portfolio/protocols")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data[0]["name"] == "Aave"
    assert "tvl" in data[0]
    assert "apy" in data[0]
    assert "positions" in data[0]


@pytest.mark.asyncio
async def test_get_portfolio_timeline():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/defi/portfolio/timeline")
    assert resp.status_code == 200
    data = resp.json()
    assert "snapshots" in data
    assert isinstance(data["snapshots"], list)
    assert "total_collateral" in data["snapshots"][0]
    assert "timestamp" in data["snapshots"][0]
