from typing import Dict

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.usefixtures("async_client_with_db")


async def _register_user(
    async_client: AsyncClient, username: str, email: str, password: str
) -> Dict[str, str]:
    """Register a user and return the response data."""
    res = await async_client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert res.status_code == 201
    return res.json()


@pytest.mark.asyncio
async def test_obtain_token_success(async_client_with_db: AsyncClient) -> None:
    """Test successful token acquisition with valid credentials."""
    username = "dana"
    password = "Sup3rStr0ng!!"
    await _register_user(
        async_client_with_db, username, f"{username}@example.com", password
    )

    res = await async_client_with_db.post(
        "/auth/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


@pytest.mark.asyncio
async def test_obtain_token_bad_credentials(async_client_with_db: AsyncClient) -> None:
    """Test token acquisition fails with invalid credentials."""
    username = "edgar"
    password = "GoodPwd1!!"
    await _register_user(
        async_client_with_db, username, f"{username}@example.com", password
    )

    res = await async_client_with_db.post(
        "/auth/token",
        data={"username": username, "password": "wrongpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 401
