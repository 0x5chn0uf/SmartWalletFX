import uuid

import pytest
from app.core.database import get_db
from app.repositories.user_repository import UserRepository
from app.utils.jwt import JWTUtils
from httpx import AsyncClient
from jose import jwt


async def _register_and_login(client: AsyncClient):
    username = f"refreshuser_{uuid.uuid4().hex[:8]}"
    password = "Str0ngP@ssw0rd!"
    email = f"{username}@example.com"

    # Register
    res = await client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert res.status_code == 201

    # Mark the user's email as verified directly in the database
    db_session = next(get_db())
    user_repo = UserRepository(db_session)
    user = await user_repo.get_by_email(email)
    user.email_verified = True
    await db_session.commit()

    # Login – obtain tokens
    res = await client.post(
        "/auth/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 200
    body = res.json()
    return body["access_token"], body["refresh_token"]


@pytest.mark.asyncio
async def test_refresh_success(async_client_with_db: AsyncClient):
    _, refresh_token = await _register_and_login(async_client_with_db)

    res = await async_client_with_db.post(
        "/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert res.status_code == 200
    body = res.json()

    # Same refresh token returned
    assert body["refresh_token"] == refresh_token
    assert body["access_token"]
    assert body["token_type"] == "bearer"

    # Verify roles claim present in new access token
    payload = jwt.get_unverified_claims(body["access_token"])
    assert "roles" in payload and payload["roles"]


@pytest.mark.asyncio
async def test_refresh_invalid_token(async_client_with_db: AsyncClient):
    invalid_token = JWTUtils.create_access_token("123")  # not a refresh token
    res = await async_client_with_db.post(
        "/auth/refresh", json={"refresh_token": invalid_token}
    )
    assert res.status_code == 401
