import httpx
import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_defi_health_endpoint():
    """DeFi health endpoint should return status ok."""
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/defi/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
