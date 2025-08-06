from __future__ import annotations

import uuid

import httpx
import pytest
import respx
from fastapi import FastAPI


@pytest.mark.asyncio
@respx.mock
async def test_google_oauth_callback(test_app_with_di_container: FastAPI, monkeypatch):
    """OAuth callback should redirect with auth cookies set."""
    state = "abc123"

    # Mock both the endpoint and usecase verify_state functions
    async def _verify_state(redis, st):
        return True

    monkeypatch.setattr("app.api.endpoints.oauth.verify_state", _verify_state)
    monkeypatch.setattr("app.usecase.oauth_usecase.verify_state", _verify_state)

    respx.post("https://oauth2.googleapis.com/token").mock(
        return_value=httpx.Response(200, json={"id_token": "dummy"})
    )
    from jose import jwt

    original = jwt.get_unverified_claims

    def fake(token: str):
        if token == "dummy":
            return {"sub": "111", "email": "g@example.com"}
        return original(token)

    monkeypatch.setattr(jwt, "get_unverified_claims", fake)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=test_app_with_di_container),
        base_url="http://test",
    ) as client:
        resp = await client.get(
            "/auth/oauth/google/callback",
            params={"code": "c", "state": state},
            cookies={"oauth_state": state},
            follow_redirects=False,
        )

        assert resp.status_code == 302
        assert resp.headers["location"].endswith("/defi")

        cookies = resp.headers.get_list("set-cookie")
        assert any(c.startswith("access_token=") for c in cookies)
        assert any(c.startswith("refresh_token=") for c in cookies)


@pytest.mark.asyncio
async def test_google_oauth_login(test_app_with_di_container: FastAPI, monkeypatch):
    """Login endpoint should redirect to provider auth URL and set state cookie."""

    # Mock both the endpoint and usecase generate_state functions
    def _generate_state():
        return "state123"

    monkeypatch.setattr("app.usecase.oauth_usecase.generate_state", _generate_state)

    async def _store_state(redis, st, ttl: int = 300):
        return True

    monkeypatch.setattr("app.usecase.oauth_usecase.store_state", _store_state)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=test_app_with_di_container),
        base_url="http://test",
    ) as client:
        resp = await client.get(
            "/auth/oauth/google/login",
            follow_redirects=False,
        )

        assert resp.status_code == 307
        assert resp.headers["location"].startswith(
            "https://accounts.google.com/o/oauth2/v2/auth"
        )
        cookies = resp.headers.get_list("set-cookie")
        assert any("oauth_state=state123" in c for c in cookies)
