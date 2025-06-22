import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_wallets_empty(authenticated_client: AsyncClient):
    """Listing wallets for a new user should return an empty list."""
    resp = await authenticated_client.get("/wallets")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_and_list_wallets(authenticated_client: AsyncClient):
    """After creating a wallet it should appear in list_wallets."""
    addr = "0x" + uuid.uuid4().hex + "d" * (40 - len(uuid.uuid4().hex))
    payload = {"address": addr, "name": "ListMe"}
    create_resp = await authenticated_client.post("/wallets", json=payload)
    assert create_resp.status_code == 201

    list_resp = await authenticated_client.get("/wallets")
    assert list_resp.status_code == 200
    wallets = list_resp.json()
    assert any(w["address"] == addr for w in wallets)


@pytest.mark.asyncio
async def test_delete_wallet_success(authenticated_client: AsyncClient):
    """User deletes their own wallet successfully."""
    addr = "0x" + uuid.uuid4().hex + "d" * (40 - len(uuid.uuid4().hex))
    resp = await authenticated_client.post(
        "/wallets", json={"address": addr, "name": "DelMe"}
    )
    assert resp.status_code == 201

    del_resp = await authenticated_client.delete(f"/wallets/{addr}")
    assert del_resp.status_code == 204

    list_resp = await authenticated_client.get("/wallets")
    assert all(w["address"] != addr for w in list_resp.json())


@pytest.mark.asyncio
async def test_delete_wallet_unauthorized(authenticated_client: AsyncClient, test_app):
    """Deleting wallet without auth returns 401."""
    addr = "0x" + uuid.uuid4().hex + "d" * (40 - len(uuid.uuid4().hex))
    resp = await authenticated_client.post(
        "/wallets", json={"address": addr, "name": "NoAuth"}
    )
    assert resp.status_code == 201

    # unauthenticated delete attempt
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        unauth = await ac.delete(f"/wallets/{addr}")
    assert unauth.status_code == 401


@pytest.mark.asyncio
async def test_delete_wallet_wrong_user(
    authenticated_client: AsyncClient, create_user_and_wallet, test_app, db_session
):
    """Other user cannot delete wallet they don't own (404)."""
    addr = "0x" + uuid.uuid4().hex + "d" * (40 - len(uuid.uuid4().hex))
    resp = await authenticated_client.post(
        "/wallets", json={"address": addr, "name": "OwnerA"}
    )
    assert resp.status_code == 201

    # user B
    from app.services.auth_service import AuthService

    user_b, _ = await create_user_and_wallet()
    token_b = await AuthService(db_session).authenticate(user_b.username, "S3cur3!pwd")
    headers_b = {"Authorization": f"Bearer {token_b.access_token}"}

    async with AsyncClient(
        app=test_app, base_url="http://test", headers=headers_b
    ) as ac_b:
        resp_b = await ac_b.delete(f"/wallets/{addr}")
    assert resp_b.status_code == 404
