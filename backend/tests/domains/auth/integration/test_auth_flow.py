import uuid
from typing import Dict

import httpx
import pytest
from fastapi import FastAPI
from jose import jwt

from tests.shared.utils.safe_client import safe_get, safe_post

pytestmark = pytest.mark.integration


@pytest.fixture
def user_payload() -> Dict[str, str]:
    unique_id = uuid.uuid4().hex[:8]
    return {
        "username": f"alice_{unique_id}",
        "email": f"alice_{unique_id}@example.com",
        "password": "Str0ng!pwd",
    }


@pytest.mark.asyncio
async def test_register_login_and_me(
    test_app_with_di_container: FastAPI,
    test_di_container_with_db,
    user_payload: Dict[str, str],
) -> None:
    """Happy-path: register → login → protected `/users/me`."""

    # Get repositories and services from DI container
    user_repo = test_di_container_with_db.get_repository("user")
    test_di_container_with_db.get_usecase("auth")

    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test"
    ) as client:
        # Register
        resp = await client.post("/auth/register", json=user_payload)
        assert resp.status_code == 201, resp.text
        user_out = resp.json()
        assert user_out["username"] == user_payload["username"]
        assert user_out["email"] == user_payload["email"]
        assert "hashed_password" not in user_out, "Sensitive field leaked in response"

        # Get the created user and verify email using repository
        user = await user_repo.get_by_email(user_payload["email"])
        user.email_verified = True
        await user_repo.save(user)

        # Login – OAuth2 Password flow expects form-encoded payload
        form = {
            "username": user_payload["username"],
            "password": user_payload["password"],
        }
        resp = await client.post(
            "/auth/token",
            data=form,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 200, resp.text
        tokens = resp.json()
        assert tokens["token_type"] == "bearer"
        assert "access_token" in tokens and tokens["access_token"]

        # Protected route (use safe_get due to ASGI issues)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        resp = await safe_get(test_app_with_di_container, "/users/me", headers=headers)
        assert resp.status_code == 200, resp.text
        me = resp.json()
        assert me["username"] == user_payload["username"]
        assert me["email"] == user_payload["email"]


@pytest.mark.asyncio
async def test_login_with_wrong_password(
    test_app_with_di_container: FastAPI,
    test_di_container_with_db,
    user_payload: Dict[str, str],
) -> None:
    """Incorrect password should yield 401."""

    # Get repositories from DI container
    user_repo = test_di_container_with_db.get_repository("user")

    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test"
    ) as client:
        # Ensure user exists
        resp = await client.post("/auth/register", json=user_payload)
        assert resp.status_code == 201

        # Mark the user's email as verified using repository
        user = await user_repo.get_by_email(user_payload["email"])
        user.email_verified = True
        await user_repo.save(user)

        bad_form = {"username": user_payload["username"], "password": "WrongPass1!"}
        resp = await safe_post(
            test_app_with_di_container,
            "/auth/token",
            data=bad_form,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 401, resp.text


@pytest.mark.asyncio
async def test_protected_route_requires_token(
    test_app_with_di_container: FastAPI,
) -> None:
    resp = await safe_get(test_app_with_di_container, "/users/me")
    assert resp.status_code == 401, resp.text


@pytest.mark.asyncio
async def test_protected_route_rejects_invalid_token(
    test_di_container_with_db,
) -> None:
    # Test the endpoint logic directly without going through HTTP layer
    from unittest.mock import Mock

    from fastapi import HTTPException, Request

    from app.api.dependencies import get_user_id_from_request

    # Create a mock request with invalid auth state
    request = Mock(spec=Request)
    request.state = Mock()
    request.state.user_id = (
        None  # This simulates what middleware sets for invalid tokens
    )

    # The get_user_id_from_request should raise HTTPException with 401
    try:
        get_user_id_from_request(request)
        assert False, "Should have raised HTTPException"
    except HTTPException as e:
        assert e.status_code == 401, f"Expected 401, got {e.status_code}"
        assert "Not authenticated" in str(e.detail), f"Unexpected detail: {e.detail}"


@pytest.mark.asyncio
async def test_access_token_contains_expected_claims(
    test_app_with_di_container: FastAPI,
    test_di_container_with_db,
    user_payload: Dict[str, str],
) -> None:
    """Verify issued access token contains required claims."""

    # Get repositories from DI container
    user_repo = test_di_container_with_db.get_repository("user")

    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test"
    ) as client:
        # First register the user
        await client.post("/auth/register", json=user_payload)

        # Mark the user's email as verified using repository
        user = await user_repo.get_by_email(user_payload["email"])
        user.email_verified = True
        await user_repo.save(user)

        resp = await client.post(
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
