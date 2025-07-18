from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from app.schemas.user import UserCreate
from app.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_password_reset_flow(
    async_client_with_db: AsyncClient, db_session, monkeypatch
) -> None:
    # Register user
    user = await AuthService(db_session).register(
        UserCreate(
            username="resetuser", email="reset@example.com", password="Str0ng!pwd"
        )
    )

    # Mark the user's email as verified
    user.email_verified = True
    await db_session.commit()

    # Patch token generator to return fixed token
    fixed_token = "fixed-token"

    async def dummy_send(self, email: str, reset_link: str) -> None:
        assert fixed_token in reset_link

    from app.api.endpoints import password_reset as ep

    ep.generate_token = lambda: (
        fixed_token,
        "hash",
        datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    # Patch using monkeypatch to ensure cleanup after the test
    monkeypatch.setattr(
        ep.EmailService, "send_password_reset", dummy_send, raising=False
    )

    resp = await async_client_with_db.post(
        "/auth/forgot-password", json={"email": user.email}
    )
    assert resp.status_code == 204

    # Reset password
    new_password = "N3wPass!123"
    resp = await async_client_with_db.post(
        "/auth/reset-password", json={"token": fixed_token, "password": new_password}
    )
    assert resp.status_code == 200

    # Login with new password should succeed
    form = {"username": user.username, "password": new_password}
    login_resp = await async_client_with_db.post(
        "/auth/token",
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_resp.status_code == 200


# ---------------------------------------------------------------------------
# Additional edge-case tests for password-reset flow (coverage → 100%)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_forgot_password_unknown_email(async_client_with_db: AsyncClient) -> None:
    """Unknown email addresses should return 204 without leaking info."""

    resp = await async_client_with_db.post(
        "/auth/forgot-password", json={"email": "unknown@example.com"}
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_password_reset_rate_limit(
    async_client_with_db: AsyncClient,
    db_session,
    monkeypatch,
) -> None:
    """Hitting the forgot-password endpoint more than the allowed attempts should 429."""

    from app.api.endpoints import password_reset as pr_ep

    # Use a tiny window/limit to keep the test fast
    pr_ep.reset_rate_limiter = pr_ep.InMemoryRateLimiter(
        max_attempts=1, window_seconds=60
    )

    # Register user
    email_unique = f"rl-{uuid.uuid4().hex[:8]}@example.com"
    username_unique = f"rluser-{uuid.uuid4().hex[:8]}"
    user = await AuthService(db_session).register(
        UserCreate(username=username_unique, email=email_unique, password="Str0ng!pwd")
    )

    # Mark the user's email as verified
    user.email_verified = True
    await db_session.commit()

    # Stub email sending to avoid I/O
    async def _dummy_send(self, email: str, link: str) -> None:  # noqa: D401 – stub
        pass

    monkeypatch.setattr(
        pr_ep.EmailService, "send_password_reset", _dummy_send, raising=False
    )

    # Ensure unique tokens to avoid DB conflict from previous tests
    def _unique_token():  # noqa: D401 – stub factory
        tok = uuid.uuid4().hex + "tok"
        from datetime import datetime, timedelta, timezone

        return tok, "unused", datetime.now(timezone.utc) + timedelta(minutes=30)

    monkeypatch.setattr(pr_ep, "generate_token", _unique_token, raising=False)

    payload = {"email": user.email}

    # First attempt allowed
    first = await async_client_with_db.post("/auth/forgot-password", json=payload)
    assert first.status_code == 204

    # Second attempt in the same window → rate-limited
    second = await async_client_with_db.post("/auth/forgot-password", json=payload)
    assert second.status_code == 429


@pytest.mark.asyncio
async def test_verify_invalid_token(async_client_with_db: AsyncClient) -> None:
    """/verify-reset-token should return `{valid: False}` for unknown tokens."""

    resp = await async_client_with_db.post(
        "/auth/verify-reset-token", json={"token": "does-not-exist"}
    )
    assert resp.status_code == 200
    assert resp.json() == {"valid": False}


@pytest.mark.asyncio
async def test_reset_password_invalid_token(async_client_with_db: AsyncClient) -> None:
    """/reset-password should reject invalid or expired tokens."""

    resp = await async_client_with_db.post(
        "/auth/reset-password",
        json={"token": "doesnotexist1", "password": "NewValid1!"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_reset_password_token_reuse(
    async_client_with_db: AsyncClient,
    db_session,
) -> None:
    """Tokens are single-use – a second attempt should fail with 400."""

    from datetime import datetime, timedelta, timezone

    from app.repositories.password_reset_repository import (
        PasswordResetRepository,
    )

    # Arrange – create user & token manually
    user = await AuthService(db_session).register(
        UserCreate(username="reuse", email="reuse@example.com", password="Str0ng!pwd")
    )

    # Mark the user's email as verified
    user.email_verified = True
    await db_session.commit()

    token = "single-use-token"
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    await PasswordResetRepository(db_session).create(token, user.id, expires_at)

    # First successful reset
    ok = await async_client_with_db.post(
        "/auth/reset-password",
        json={"token": token, "password": "BrandN3w!pwd"},
    )
    assert ok.status_code == 200

    # Second attempt should now fail (token marked as used)
    fail = await async_client_with_db.post(
        "/auth/reset-password",
        json={"token": token, "password": "Another1!pwd"},
    )
    assert fail.status_code == 400
