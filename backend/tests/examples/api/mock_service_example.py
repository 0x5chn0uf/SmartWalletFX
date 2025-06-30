import pytest

from tests.fixtures import async_client, mock_httpx_client


@pytest.mark.asyncio
async def test_health_endpoint_httpx_mocked(mock_httpx_client, async_client):
    # External HTTPX calls are mocked by fixture
    resp = await async_client.get("/defi/health")
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"  # based on health endpoint response
