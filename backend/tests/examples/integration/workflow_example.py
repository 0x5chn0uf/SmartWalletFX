import pytest



@pytest.mark.asyncio
async def test_user_end_to_end_flow(async_client):
    # Register user
    payload = {
        "username": "flowuser",
        "email": "flow@example.com",
        "password": "FlowPwd1!",
    }
    reg = await async_client.post("/auth/register", json=payload)
    assert reg.status_code == 201

    # Login and retrieve token
    login = await async_client.post(
        "/auth/token",
        data={"username": payload["username"], "password": payload["password"]},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Retrieve user profile
    profile = await async_client.get("/users/me", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["username"] == payload["username"]
