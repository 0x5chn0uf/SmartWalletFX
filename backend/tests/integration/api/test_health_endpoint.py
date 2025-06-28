import httpx
import pytest


@pytest.mark.asyncio
async def test_health_endpoint(test_app):
    """Health check should return {'status': 'ok'} with 200."""
    transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=True)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as ac:
        resp = await ac.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
