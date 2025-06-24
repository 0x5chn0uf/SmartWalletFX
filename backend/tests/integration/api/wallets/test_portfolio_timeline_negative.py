import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_portfolio_timeline_unauthorized(
    authenticated_client: AsyncClient, test_app
):
    """Accessing timeline without auth should return 401."""
    # Create wallet with authenticated client
    unique_hex = uuid.uuid4().hex
    addr = "0x" + unique_hex + "d" * (40 - len(unique_hex))
    resp = await authenticated_client.post(
        "/wallets", json={"address": addr, "name": "Timeline"}
    )
    assert resp.status_code == 201

    # Unauthenticated request
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        r = await ac.get(f"/wallets/{addr}/portfolio/timeline")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_portfolio_timeline_wrong_user(
    authenticated_client: AsyncClient, create_user_and_wallet, test_app, db_session
):
    """User B cannot access User A's timeline."""
    unique_hex = uuid.uuid4().hex
    addr = "0x" + unique_hex + "d" * (40 - len(unique_hex))
    resp = await authenticated_client.post(
        "/wallets", json={"address": addr, "name": "A Wallet"}
    )
    assert resp.status_code == 201

    # new user B
    from app.services.auth_service import AuthService

    user_b, _ = await create_user_and_wallet()
    token_b = await AuthService(db_session).authenticate(user_b.username, "S3cur3!pwd")
    headers_b = {"Authorization": f"Bearer {token_b.access_token}"}

    async with AsyncClient(
        app=test_app, base_url="http://test", headers=headers_b
    ) as ac_b:
        resp_b = await ac_b.get(f"/wallets/{addr}/portfolio/timeline")
    assert resp_b.status_code == 404


@pytest.mark.asyncio
async def test_portfolio_timeline_wallet_not_found(authenticated_client: AsyncClient):
    """Requesting timeline for non-existing wallet returns 404."""
    non_existing = "0x" + uuid.uuid4().hex + "d" * (40 - len(uuid.uuid4().hex))
    r = await authenticated_client.get(f"/wallets/{non_existing}/portfolio/timeline")
    assert r.status_code == 404
