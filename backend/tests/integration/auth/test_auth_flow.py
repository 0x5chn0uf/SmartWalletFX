from typing import Dict

import pytest
from httpx import AsyncClient
from jose import jwt


@pytest.fixture
def user_payload() -> Dict[str, str]:
    return {
        "username": "alice",
        "email": "alice@example.com",
        "password": "Str0ng!pwd",
    }


@pytest.mark.asyncio
async def test_register_login_and_me(
    async_client_with_db: AsyncClient, user_payload: Dict[str, str]
) -> None:
    """Happy-path: register → login → protected `/users/me`."""

    # Register
    resp = await async_client_with_db.post("/auth/register", json=user_payload)
    assert resp.status_code == 201, resp.text
    user_out = resp.json()
    assert user_out["username"] == user_payload["username"]
    assert user_out["email"] == user_payload["email"]
    assert "hashed_password" not in user_out, "Sensitive field leaked in response"

    # Login – OAuth2 Password flow expects form-encoded payload
    form = {
        "username": user_payload["username"],
        "password": user_payload["password"],
    }
    resp = await async_client_with_db.post(
        "/auth/token",
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200, resp.text
    tokens = resp.json()
    assert tokens["token_type"] == "bearer"
    assert "access_token" in tokens and tokens["access_token"]

    # Protected route
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = await async_client_with_db.get("/users/me", headers=headers)
    assert resp.status_code == 200, resp.text
    me = resp.json()
    assert me["username"] == user_payload["username"]
    assert me["email"] == user_payload["email"]


@pytest.mark.asyncio
async def test_login_with_wrong_password(
    async_client_with_db: AsyncClient, user_payload: Dict[str, str]
) -> None:
    """Incorrect password should yield 401."""
    # Ensure user exists
    await async_client_with_db.post("/auth/register", json=user_payload)

    bad_form = {"username": user_payload["username"], "password": "WrongPass1!"}
    resp = await async_client_with_db.post(
        "/auth/token",
        data=bad_form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 401, resp.text


@pytest.mark.asyncio
async def test_protected_route_requires_token(
    async_client_with_db: AsyncClient,
) -> None:
    resp = await async_client_with_db.get("/users/me")
    assert resp.status_code == 401, resp.text


@pytest.mark.asyncio
async def test_protected_route_rejects_invalid_token(
    async_client_with_db: AsyncClient,
) -> None:
    headers = {"Authorization": "Bearer invalid.token.here"}
    resp = await async_client_with_db.get("/users/me", headers=headers)
    assert resp.status_code == 401, resp.text


@pytest.mark.asyncio
async def test_access_token_contains_expected_claims(
    async_client_with_db: AsyncClient, user_payload: Dict[str, str]
) -> None:
    """Verify issued access token contains required claims."""
    # First register the user
    await async_client_with_db.post("/auth/register", json=user_payload)

    resp = await async_client_with_db.post(
        "/auth/token",
        data={
            "username": user_payload["username"],
            "password": user_payload["password"],
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    tokens = resp.json()

    payload = jwt.get_unverified_claims(tokens["access_token"])
    assert payload["sub"]  # subject present
    assert payload["type"] == "access"
    assert "jti" in payload
    assert "exp" in payload
