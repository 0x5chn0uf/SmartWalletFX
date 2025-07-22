from __future__ import annotations

import uuid

import httpx
import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.domain.schemas.user import UserCreate, WeakPasswordError
from app.utils.jwt import JWTUtils
from app.utils.rate_limiter import login_rate_limiter


@pytest.fixture(autouse=True)
async def _cleanup_auth_state():
    """Reset auth-related state between tests."""
    # Reset rate-limiter to avoid bleed-through from other tests
    login_rate_limiter.clear()

    # Clear cached JWT keys so downstream tests can reconfigure safely
    # Note: JWTUtils methods are no longer cached, so no cache clearing needed

    yield


@pytest.mark.parametrize(
    "payload, expected_status",
    [
        (
            {
                "username": f"dave_{uuid.uuid4().hex[:8]}",
                "email": f"dave_{uuid.uuid4().hex[:8]}@example.com",
                "password": "Str0ng!pwd",
            },
            201,
        ),
        (
            # weak password – should be rejected by validation layer
            {
                "username": f"weak_{uuid.uuid4().hex[:8]}",
                "email": f"weak_{uuid.uuid4().hex[:8]}@example.com",
                "password": "weakpass",
            },
            400,
        ),
    ],
)
@pytest.mark.asyncio
async def test_register_endpoint(
    test_app_with_di_container: FastAPI, payload: dict, expected_status: int
) -> None:
    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test"
    ) as client:
        resp = await client.post("/auth/register", json=payload)
        assert resp.status_code == expected_status
        if expected_status == 201:
            body = resp.json()
            assert body["username"] == payload["username"]
            assert body["email"] == payload["email"]
            assert "hashed_password" not in body


@pytest.mark.asyncio
async def test_register_duplicate_email(
    test_app_with_di_container: FastAPI,
) -> None:
    unique_id = uuid.uuid4().hex[:8]
    payload1 = {
        "username": f"erin_{unique_id}",
        "email": f"erin_{unique_id}@example.com",
        "password": "Str0ng!pwd",
    }
    payload2 = {
        "username": f"erin2_{unique_id}",
        "email": f"erin_{unique_id}@example.com",
        "password": "Str0ng!pwd",
    }

    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test"
    ) as client:
        assert (await client.post("/auth/register", json=payload1)).status_code == 201
        dup_resp = await client.post("/auth/register", json=payload2)
        assert dup_resp.status_code == 409


@pytest.mark.asyncio
async def test_obtain_token_success(
    test_app_with_di_container, test_di_container_with_db
) -> None:
    # Get repositories and services from DIContainer
    user_repo = test_di_container_with_db.get_repository("user")
    auth_usecase = test_di_container_with_db.get_usecase("auth")

    username = f"tokenuser-{uuid.uuid4().hex[:8]}"
    password = "Str0ng!pwd"
    email = f"token-{uuid.uuid4().hex[:8]}@ex.com"

    # Arrange – create user via service
    user = await auth_usecase.register(
        UserCreate(
            username=username,
            email=email,
            password=password,
        )
    )
    # Mark email verified for test login
    user.email_verified = True
    await user_repo.save(user)

    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test"
    ) as client:
        data = {"username": username, "password": password}
        resp = await client.post("/auth/token", data=data)
        assert resp.status_code == 200
        body = resp.json()
        assert body["token_type"] == "bearer"
        assert all(k in body for k in ("access_token", "refresh_token", "expires_in"))


@pytest.mark.asyncio
async def test_login_rate_limit(
    test_app_with_di_container, test_di_container_with_db
) -> None:
    """Test that login rate limiting works correctly."""
    # Get the rate limiter from DI container to control it for testing
    rate_limiter_utils = test_di_container_with_db.get_utility("rate_limiter_utils")
    auth_usecase = test_di_container_with_db.get_usecase("auth")

    # Clear any existing rate limit state
    rate_limiter_utils.login_rate_limiter.clear()

    # Create a test user
    user_create = UserCreate(
        username=f"ratetest-{uuid.uuid4().hex[:8]}",
        email=f"ratetest-{uuid.uuid4().hex[:8]}@example.com",
        password="StrongPassword123!",
    )
    user = await auth_usecase.register(user_create)
    user.email_verified = True

    # Commit the user to the database
    user_repo = test_di_container_with_db.get_repository("user")
    await user_repo.save(user)

    async with AsyncClient(
        app=test_app_with_di_container, base_url="http://test"
    ) as client:
        # Test successful logins don't trigger rate limit
        form_data = {"username": user.username, "password": "StrongPassword123!"}
        resp = await client.post(
            "/auth/token",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 200

        # Clear rate limiter again to start fresh
        rate_limiter_utils.login_rate_limiter.clear()

        # Test failed logins trigger rate limit
        bad_form_data = {"username": user.username, "password": "WrongPassword"}

        # Should allow initial failed attempts (up to max_attempts)
        for i in range(5):  # AUTH_RATE_LIMIT_ATTEMPTS default is 5
            resp = await client.post(
                "/auth/token",
                data=bad_form_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            assert resp.status_code == 401  # Wrong credentials

        # Next attempt should be rate limited
        resp = await client.post(
            "/auth/token",
            data=bad_form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 429  # Rate limited


@pytest.mark.asyncio
async def test_users_me_endpoint(
    test_app_with_di_container, test_di_container_with_db
) -> None:
    """/users/me should require auth and return current profile when token provided."""
    # Get repositories and services from DIContainer
    user_repo = test_di_container_with_db.get_repository("user")
    auth_usecase = test_di_container_with_db.get_usecase("auth")

    username = f"meuser-{uuid.uuid4().hex[:8]}"
    email = f"me-{uuid.uuid4().hex[:8]}@ex.com"

    # Register user & obtain token
    user = await auth_usecase.register(
        UserCreate(username=username, email=email, password="Str0ng!pwd")
    )
    # Mark email verified for test login
    user.email_verified = True
    await user_repo.save(user)

    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test"
    ) as client:
        token_resp = await client.post(
            "/auth/token", data={"username": username, "password": "Str0ng!pwd"}
        )
        assert token_resp.status_code == 200
        access_token = token_resp.json()["access_token"]

        # 1. Missing token → 401
        unauth = await client.get("/users/me")
        assert unauth.status_code == 401

        # 2. Valid token → 200 with expected fields
        headers = {"Authorization": f"Bearer {access_token}"}
        auth_resp = await client.get("/users/me", headers=headers)
        assert auth_resp.status_code == 200
        body = auth_resp.json()
        assert body["username"] == username
        assert body["email"] == email
    assert "hashed_password" not in body


@pytest.mark.asyncio
async def test_token_invalid_credentials(test_app_with_di_container: FastAPI) -> None:
    data = {"username": f"fake_{uuid.uuid4().hex[:8]}", "password": "wrong"}
    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test"
    ) as client:
        resp = await client.post("/auth/token", data=data)
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_token_inactive_user(
    test_app_with_di_container: FastAPI, test_di_container_with_db
) -> None:
    username = f"inactive_{uuid.uuid4().hex[:8]}"
    email = f"inactive-{uuid.uuid4().hex[:8]}@ex.com"
    password = "Str0ng!pwd"

    # Get repositories and services from DI container
    user_repo = test_di_container_with_db.get_repository("user")
    auth_usecase = test_di_container_with_db.get_usecase("auth")

    # Create an inactive user
    user_data = UserCreate(username=username, email=email, password=password)
    user = await auth_usecase.register(user_data)

    # Make the user inactive using repository
    user.is_active = False
    await user_repo.save(user)

    # Test login with inactive user
    data = {"username": username, "password": password}
    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test"
    ) as client:
        resp = await client.post("/auth/token", data=data)

    assert resp.status_code == 403  # Inactive users get 403, not 401


@pytest.mark.asyncio
async def test_token_unverified_email(
    test_app_with_di_container: FastAPI, test_di_container_with_db
) -> None:
    username = f"unverified_{uuid.uuid4().hex[:8]}"
    email = f"unverified-{uuid.uuid4().hex[:8]}@ex.com"
    password = "Str0ng!pwd"

    # Get repositories and services from DI container
    user_repo = test_di_container_with_db.get_repository("user")
    auth_usecase = test_di_container_with_db.get_usecase("auth")

    # Create a user with unverified email
    user_data = UserCreate(username=username, email=email, password=password)
    user = await auth_usecase.register(user_data)

    # Make sure email is not verified (this should be the default)
    user.email_verified = False
    await user_repo.save(user)

    # Test login with unverified email
    data = {"username": username, "password": password}
    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test"
    ) as client:
        resp = await client.post("/auth/token", data=data)

    assert resp.status_code == 403  # Unverified email should return 403, not 401
    detail = resp.json()["detail"].lower()
    assert (
        "email" in detail and "verified" in detail
    )  # Check for email verification message


@pytest.mark.asyncio
async def test_register_weak_password_error(
    test_app_with_di_container: FastAPI,
    monkeypatch,
) -> None:
    """Check that a WeakPasswordError from service is handled as 400."""

    async def _raise_weak(self, payload, **kwargs):  # noqa: D401 – stub
        raise WeakPasswordError("Password is too weak")

    monkeypatch.setattr("app.usecase.auth_usecase.AuthUsecase.register", _raise_weak)

    payload = {
        "username": f"user_{uuid.uuid4().hex[:8]}",
        "email": f"email_{uuid.uuid4().hex[:8]}@example.com",
        "password": "@ny-Password123!",
    }
    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test"
    ) as client:
        resp = await client.post("/auth/register", json=payload)

    assert resp.status_code == 400
    assert "strength requirements" in resp.json()["detail"]
