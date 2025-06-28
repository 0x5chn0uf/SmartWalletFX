import pytest

from tests.fixtures import client


@pytest.mark.anyio
def test_health_endpoint(client):
    resp = client.get("/defi/health")
    assert resp.status_code == 200
