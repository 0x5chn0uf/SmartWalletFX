import pytest


@pytest.mark.asyncio
def test_health_endpoint(client):
    resp = client.get("/defi/health")
    assert resp.status_code == 200
