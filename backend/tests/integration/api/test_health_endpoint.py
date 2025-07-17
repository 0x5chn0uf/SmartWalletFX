import pytest


@pytest.mark.asyncio
async def test_health_endpoint_with_di_container(integration_async_client):
    """Health check using DIContainer pattern should return {'status': 'ok'} with 200."""
    resp = await integration_async_client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
