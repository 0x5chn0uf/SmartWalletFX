import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_portfolio_metrics_and_timeline(authenticated_client: AsyncClient):
    """Full flow: create wallet, then fetch portfolio metrics & timeline."""
    # 1. Create a unique wallet for the authenticated user
    unique_hex = uuid.uuid4().hex  # 32 chars
    unique_address = "0x" + unique_hex + "d" * (40 - len(unique_hex))
    wallet_payload = {"address": unique_address, "name": "Metrics Wallet"}
    resp = await authenticated_client.post("/wallets", json=wallet_payload)
    assert resp.status_code == 201

    # 2. Retrieve portfolio metrics
    metrics_resp = await authenticated_client.get(
        f"/wallets/{unique_address}/portfolio/metrics"
    )
    assert metrics_resp.status_code == 200
    metrics = metrics_resp.json()
    assert metrics["user_address"] == unique_address
    # Collateral & borrowings might be 0 in an empty DB but keys must exist
    for field in [
        "total_collateral",
        "total_borrowings",
        "total_collateral_usd",
        "total_borrowings_usd",
    ]:
        assert field in metrics

    # 3. Retrieve portfolio timeline
    timeline_resp = await authenticated_client.get(
        f"/wallets/{unique_address}/portfolio/timeline?interval=daily&limit=10"
    )
    assert timeline_resp.status_code == 200
    timeline = timeline_resp.json()
    # Expect lists in timeline response
    assert "timestamps" in timeline
    assert "collateral_usd" in timeline
    assert "borrowings_usd" in timeline
    # Length consistency
    assert (
        len(timeline["timestamps"])
        == len(timeline["collateral_usd"])
        == len(timeline["borrowings_usd"])
    )
