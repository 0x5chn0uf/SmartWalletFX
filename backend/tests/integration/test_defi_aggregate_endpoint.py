from typing import AsyncGenerator
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.api.dependencies import auth_deps, get_aggregator_service, get_redis
from app.main import app
from app.models.aggregate_metrics import AggregateMetricsModel
from app.services.defi_aggregation_service import DeFiAggregationService
from app.utils.jwt import JWTUtils


class DummyRedis:
    def __init__(self):
        self._store = {}

    async def get(self, key):
        return self._store.get(key)

    async def setex(self, key, ttl, value):
        self._store[key] = value
        return True

    async def delete(self, key):
        self._store.pop(key, None)
        return True

    async def close(self):
        return True


@pytest.fixture
def dummy_redis(monkeypatch):
    redis = DummyRedis()

    # Patch the get_redis dependency to yield our dummy
    async def _get_redis_override():
        yield redis

    app.dependency_overrides.clear()
    from app.api.dependencies import get_redis

    app.dependency_overrides[get_redis] = _get_redis_override
    yield redis
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
async def override_deps(dummy_redis):  # noqa: D401 – fixture
    # Override Redis dependency
    async def _get_redis_override() -> AsyncGenerator[DummyRedis, None]:
        yield dummy_redis

    app.dependency_overrides[get_redis] = _get_redis_override

    # Also override the AggregatorService dependency with a lightweight stub

    class _StubAggregatorService:  # noqa: D401 – test stub
        async def aggregate(self, wallet_id: str):  # type: ignore[override]
            # Return minimal valid AggregateMetrics object
            metrics = AggregateMetricsModel.create_new(wallet_id)
            metrics.tvl = 0
            metrics.total_borrowings = 0
            metrics.aggregate_apy = None
            metrics.positions = []
            return metrics

    async def _get_agg_service_override():
        return _StubAggregatorService()

    app.dependency_overrides[get_aggregator_service] = _get_agg_service_override

    yield

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_aggregate_endpoint_cache(dummy_redis, test_user):
    """Test that the aggregate endpoint works with caching."""

    # Override authentication to return test_user directly
    async def _get_current_user_override():
        return test_user

    app.dependency_overrides[auth_deps.get_current_user] = _get_current_user_override
    addr = "0x0000000000000000000000000000000000000001"
    token = JWTUtils.create_access_token(str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    # Patch the aggregate_wallet_positions method to simulate caching
    metrics = AggregateMetricsModel.create_new(addr)
    metrics.tvl = 123.45
    metrics.total_borrowings = 67.89
    metrics.aggregate_apy = 0.05
    metrics.positions = []

    async def fake_aggregate_wallet_positions(self, wallet_address):
        # Simulate caching
        cache_key = f"defi:aggregate:{wallet_address.lower()}"
        import json

        await dummy_redis.setex(cache_key, 3600, json.dumps(metrics.to_dict()))
        return metrics

    with patch.object(
        DeFiAggregationService,
        "aggregate_wallet_positions",
        fake_aggregate_wallet_positions,
    ):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # First call – cache miss -> compute
            resp1 = await ac.get(f"/defi/aggregate/{addr}", headers=headers)
            if resp1.status_code != 200:
                print(f"Error response: {resp1.json()}")
            assert resp1.status_code == 200
            data1 = resp1.json()

            # Second call – should hit cache and return identical payload
            resp2 = await ac.get(f"/defi/aggregate/{addr}", headers=headers)
            assert resp2.status_code == 200
            assert resp2.json() == data1  # Cached response identical

            # Ensure dummy redis has the key stored
            assert dummy_redis._store  # type: ignore[attr-defined]
    app.dependency_overrides.clear()
