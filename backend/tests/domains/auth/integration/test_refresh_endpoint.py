import uuid

import httpx
import pytest
from fastapi import FastAPI
from jose import jwt

from app.domain.schemas.user import UserCreate
from app.utils.rate_limiter import login_rate_limiter
from tests.shared.utils.safe_client import safe_post

pytestmark = pytest.mark.integration


async def _register_and_login_with_di(
    client: httpx.AsyncClient,
    test_di_container_with_db,
    email: str,
    username: str,
    password: str,
):
    """Register and login using DI container services."""
    # Get auth usecase from DI container
    auth_usecase = test_di_container_with_db.get_usecase("auth")

    # Register user
    await auth_usecase.register(
        UserCreate(username=username, email=email, password=password)
    )

    # Get user repository from DI container and mark email as verified
    user_repo = test_di_container_with_db.get_repository("user")
    db_user = await user_repo.get_by_email(email)
    if db_user:
        db_user.email_verified = True
        await user_repo.save(db_user)

    # Login – obtain tokens
    res = await client.post(
        "/auth/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 200
    body = res.json()
    return body["access_token"], body["refresh_token"]


# @pytest.mark.skip(reason="Application issue: AuthService missing refresh_token method")
@pytest.mark.asyncio
async def test_refresh_success(
    test_app_with_di_container: FastAPI, test_di_container_with_db
):
    username = f"refreshuser_{uuid.uuid4().hex[:8]}"
    password = "Str0ngP@ssw0rd!"
    email = f"{username}@example.com"

    transport = httpx.ASGITransport(app=test_app_with_di_container)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        _, refresh_token = await _register_and_login_with_di(
            client, test_di_container_with_db, email, username, password
        )

        res = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert res.status_code == 200
        body = res.json()
        assert "access_token" in body
        assert "refresh_token" in body

        # Ensure the new access token is valid JWT
        decoded = jwt.decode(
            body["access_token"],
            key="dummy",  # Not used since verify_signature=False
            options={"verify_signature": False, "verify_exp": False},
        )
        assert "sub" in decoded
        assert "roles" in decoded


@pytest.mark.asyncio
async def test_refresh_invalid_token(test_app_with_di_container: FastAPI):
    res = await safe_post(
        test_app_with_di_container,
        "/auth/refresh",
        json={"refresh_token": "invalid-token"},
    )
    assert res.status_code == 401
    assert "Invalid refresh token" in res.json().get("detail", "")
