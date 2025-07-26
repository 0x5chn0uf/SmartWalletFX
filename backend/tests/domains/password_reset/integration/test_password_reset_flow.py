from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from app.domain.schemas.user import UserCreate

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_password_reset_flow(
    test_app_with_di_container, test_di_container_with_db
) -> None:
    # Use DI container for consistent session handling
    from httpx import AsyncClient

    # Register user using DI container
    unique_id = uuid.uuid4().hex[:8]
    email = f"reset_{unique_id}@example.com"
    username = f"resetuser_{unique_id}"

    auth_usecase = test_di_container_with_db.get_usecase("auth")
    user = await auth_usecase.register(
        UserCreate(
            username=username,
            email=email,
            password="Str0ng!pwd",
        )
    )

    # Mark email as verified using DI container
    user_repo = test_di_container_with_db.get_repository("user")
    db_user = await user_repo.get_by_email(email)
    if db_user:
        db_user.email_verified = True
        await user_repo.save(db_user)

    # Use async client with the DI container app
    async with AsyncClient(
        app=test_app_with_di_container, base_url="http://test"
    ) as client:
        # Small delay to ensure all transactions are committed
        import asyncio

        await asyncio.sleep(0.1)

        # Patch token generator to return fixed token with unique hash
        fixed_token = f"fixed-token-{unique_id}"
        token_hash = f"hash-{unique_id}"

        async def dummy_send(self, email: str, reset_link: str) -> None:
            assert fixed_token in reset_link

        from unittest.mock import patch

        from app.api.endpoints import password_reset as ep

        # This direct patching is not ideal with DI, but we'll keep it for now
        # to minimize the scope of changes.
        with patch.object(
            ep,
            "generate_token",
            return_value=(
                fixed_token,
                token_hash,
                datetime.now(timezone.utc) + timedelta(minutes=30),
            ),
        ):
            # Patch email service
            with patch.object(ep.EmailService, "send_password_reset", dummy_send):
                resp = await client.post(
                    "/auth/password-reset-request", json={"email": email}
                )
                assert resp.status_code == 204

                # Reset password
                new_password = "N3wPass!123"
                resp = await client.post(
                    "/auth/password-reset-complete",
                    json={"token": fixed_token, "password": new_password},
                )
                assert resp.status_code == 200

                # Login with new password should succeed
                form = {"username": user.username, "password": new_password}
                login_resp = await client.post(
                    "/auth/token",
                    data=form,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                assert login_resp.status_code == 200


# ---------------------------------------------------------------------------
# Additional edge-case tests for password-reset flow (coverage → 100%)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_forgot_password_unknown_email(
    integration_async_client: AsyncClient,
) -> None:
    """Unknown email addresses should return 204 without leaking info."""

    resp = await integration_async_client.post(
        "/auth/password-reset-request", json={"email": "unknown@example.com"}
    )
    # Should return 204 to avoid leaking email info
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_password_reset_rate_limit(
    integration_async_client, test_di_container_with_db
) -> None:
    """Hitting the forgot-password endpoint more than the allowed attempts should 429"""
    # Create a test user
    auth_usecase = test_di_container_with_db.get_usecase("auth")
    user_repo = test_di_container_with_db.get_repository("user")

    unique_id = uuid.uuid4().hex[:8]
    email = f"ratelimit_{unique_id}@example.com"
    user_create = UserCreate(
        username=f"ratelimituser_{unique_id}",
        email=email,
        password="StrongPassword123!",
    )
    user = await auth_usecase.register(user_create)
    user.email_verified = True

    # Commit the user to the database
    await user_repo.save(user)

    # Small delay to ensure database is committed
    import asyncio

    await asyncio.sleep(0.1)

    # Clear any mock state that might interfere
    import tests.conftest as conftest_module

    if hasattr(conftest_module, "_password_reset_attempts"):
        conftest_module._password_reset_attempts.clear()

    # Make password reset requests up to the limit (5 attempts)
    for i in range(5):
        resp = await integration_async_client.post(
            "/auth/password-reset-request", json={"email": email}
        )
        assert resp.status_code == 204, f"Request {i+1} should succeed"

    # Next attempt should be rate limited
    resp = await integration_async_client.post(
        "/auth/password-reset-request", json={"email": email}
    )
    assert resp.status_code == 429, "6th request should be rate limited"


@pytest.mark.asyncio
async def test_verify_invalid_token(integration_async_client: AsyncClient) -> None:
    """/password-reset-verify should return 400 for unknown tokens."""

    resp = await integration_async_client.post(
        "/auth/password-reset-verify", json={"token": "does-not-exist"}
    )
    # Should return 400 for invalid token
    assert resp.status_code == 400
    assert "Invalid or expired token" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_reset_password_invalid_token(
    integration_async_client: AsyncClient,
) -> None:
    """/password-reset-complete should reject invalid or expired tokens."""

    resp = await integration_async_client.post(
        "/auth/password-reset-complete",
        json={"token": "doesnotexist1", "password": "NewValid1!"},
    )
    # Should return 400 for invalid token
    assert resp.status_code == 400
    assert "Invalid or expired token" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_reset_password_token_reuse(
    integration_async_client, test_di_container_with_db
) -> None:
    """Tokens are single-use – a second attempt should fail with 400."""

    # Create a user for the test (required for endpoint validation)
    auth_usecase = test_di_container_with_db.get_usecase("auth")
    user_repo = test_di_container_with_db.get_repository("user")

    unique_id = uuid.uuid4().hex[:8]
    user = await auth_usecase.register(
        UserCreate(
            username=f"reuse_{unique_id}",
            email=f"reuse_{unique_id}@example.com",
            password="Str0ng!pwd",
        )
    )
    user.email_verified = True
    await user_repo.save(user)

    # Use a token that will be handled by the mock system for token reuse testing
    # This tests the integration behavior when the async client handles requests
    token = "test-reuse-token-12345"

    # Clear any existing token state in the mock
    import tests.conftest as conftest_module

    if hasattr(conftest_module, "_used_reset_tokens"):
        conftest_module._used_reset_tokens.clear()

    # First reset should succeed
    ok = await integration_async_client.post(
        "/auth/password-reset-complete",
        json={"token": token, "password": "BrandN3w!pwd"},
    )
    assert ok.status_code == 200

    # Second attempt should fail (token marked as used)
    fail = await integration_async_client.post(
        "/auth/password-reset-complete",
        json={"token": token, "password": "Another1!pwd"},
    )
    assert fail.status_code == 400
    detail = fail.json()["detail"]
    assert (
        "Reset token has already been used" in detail
        or "Invalid or expired token" in detail
    )
