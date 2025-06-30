import pytest

from tests.fixtures import client


@pytest.mark.asyncio
async def test_user_registration_and_token(client):
    payload = {
        "username": "alice",
        "email": "alice@example.com",
        "password": "Str0ng!pwd",
    }
    # Register user
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 201
    # Obtain tokens
    token_resp = client.post(
        "/auth/token",
        data={"username": payload["username"], "password": payload["password"]},
    )
    assert token_resp.status_code == 200
    data = token_resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
