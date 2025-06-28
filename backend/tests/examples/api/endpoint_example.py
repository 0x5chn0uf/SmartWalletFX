import pytest

from tests.fixtures import async_client


@pytest.mark.anyio
async def test_protected_route_requires_auth(async_client):
    # Attempt to access protected route without token
    resp = await async_client.get("/users/me")
    assert resp.status_code == 401

    # Register and login to get token
    payload = {
        "username": "user_api",
        "email": "user_api@example.com",
        "password": "ApiPwd1!",
    }
    reg_resp = await async_client.post("/auth/register", json=payload)
    assert reg_resp.status_code == 201
    login_resp = await async_client.post(
        "/auth/token",
        data={"username": payload["username"], "password": payload["password"]},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # Access protected route with token
    headers = {"Authorization": f"Bearer {token}"}
    auth_resp = await async_client.get("/users/me", headers=headers)
    assert auth_resp.status_code == 200
    assert auth_resp.json()["username"] == payload["username"]
