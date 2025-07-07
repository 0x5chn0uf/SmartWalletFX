from __future__ import annotations


import pytest
from httpx import AsyncClient

from datetime import datetime, timedelta, timezone

from app.schemas.user import UserCreate
from app.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_password_reset_flow(async_client_with_db: AsyncClient, db_session) -> None:
    # Register user
    user = await AuthService(db_session).register(
        UserCreate(username="resetuser", email="reset@example.com", password="Str0ng!pwd")
    )

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
    ep.EmailService.send_password_reset = dummy_send  # type: ignore

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
        "/auth/token", data=form, headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert login_resp.status_code == 200
