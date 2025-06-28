import pytest


@pytest.mark.benchmark(group="health")
def test_health_endpoint_performance(benchmark, client):
    # Benchmark the health endpoint and assert response
    resp = benchmark(client.get, "/defi/health")
    assert resp.status_code == 200
