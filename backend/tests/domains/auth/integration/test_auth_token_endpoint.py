import uuid
from typing import Dict

import httpx
import pytest
from fastapi import FastAPI

from app.domain.schemas.user import UserCreate
from app.utils.rate_limiter import login_rate_limiter
from tests.shared.utils.safe_client import safe_post

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_obtain_token_success(
    test_app_with_di_container: FastAPI, test_di_container_with_db
) -> None:
    """Test successful token acquisition with valid credentials."""
    unique_id = uuid.uuid4().hex[:8]
    username = f"dana_{unique_id}"
    password = "Sup3rStr0ng!!"
    email = f"{username}@example.com"

    # Get repositories and services from DI container
    user_repo = test_di_container_with_db.get_repository("user")
    auth_usecase = test_di_container_with_db.get_usecase("auth")

    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test"
    ) as client:
        # Register user using auth usecase
        user_data = UserCreate(username=username, email=email, password=password)
        user = await auth_usecase.register(user_data)

        # Verify email using repository
        user.email_verified = True
        await user_repo.save(user)

        res = await client.post(
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
async def test_obtain_token_bad_credentials(
    test_app_with_di_container: FastAPI, test_di_container_with_db
) -> None:
    """Test token acquisition fails with invalid credentials."""
    unique_id = uuid.uuid4().hex[:8]
    username = f"edgar_{unique_id}"
    password = "GoodPwd1!!"
    email = f"{username}@example.com"

    # Get repositories and services from DI container
    user_repo = test_di_container_with_db.get_repository("user")
    auth_usecase = test_di_container_with_db.get_usecase("auth")

    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test"
    ):
        # Register user using auth usecase
        user_data = UserCreate(username=username, email=email, password=password)
        user = await auth_usecase.register(user_data)

        # Mark the user's email as verified using repository
        user.email_verified = True
        await user_repo.save(user)

        res = await safe_post(
            test_app_with_di_container,
            "/auth/token",
            data={"username": username, "password": "wrongpass"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert res.status_code == 401
