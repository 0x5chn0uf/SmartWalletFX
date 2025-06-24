import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_portfolio_metrics_unauthorized(
    authenticated_client: AsyncClient, test_app
):
    """Attempt to access portfolio metrics without authentication should return 401."""
    # Create wallet with authenticated user first
    wallet_addr = "0x" + uuid.uuid4().hex + "d" * (40 - len(uuid.uuid4().hex))
    resp = await authenticated_client.post(
        "/wallets", json={"address": wallet_addr, "name": "Unauthz"}
    )
    assert resp.status_code == 201

    # Call metrics endpoint WITHOUT auth header
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        unauth_resp = await ac.get(f"/wallets/{wallet_addr}/portfolio/metrics")
    assert unauth_resp.status_code == 401


@pytest.mark.asyncio
async def test_portfolio_metrics_wrong_user(
    authenticated_client: AsyncClient, create_user_and_wallet, test_app, db_session
):
    """User B should not access User A's wallet metrics (expect 404)."""
    # User A (authenticated_client) creates a wallet
    wallet_addr = "0x" + uuid.uuid4().hex + "d" * (40 - len(uuid.uuid4().hex))
    resp = await authenticated_client.post(
        "/wallets", json={"address": wallet_addr, "name": "UserA Wallet"}
    )
    assert resp.status_code == 201

    # Create User B and generate auth token
    from app.services.auth_service import AuthService

    user_b, _ = await create_user_and_wallet()

    service = AuthService(db_session)
    token_data = await service.authenticate(user_b.username, "S3cur3!pwd")
    headers_b = {"Authorization": f"Bearer {token_data.access_token}"}

    # User B tries to access User A's wallet metrics
    async with AsyncClient(
        app=test_app, base_url="http://test", headers=headers_b
    ) as ac_b:
        resp_b = await ac_b.get(f"/wallets/{wallet_addr}/portfolio/metrics")

    # Should return 404 (wallet not found or not permitted)
    assert resp_b.status_code == 404
