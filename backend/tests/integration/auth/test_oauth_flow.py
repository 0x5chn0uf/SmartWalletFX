from __future__ import annotations

import uuid

import httpx
import respx
import pytest
from httpx import AsyncClient

from app.core.config import settings


@pytest.mark.asyncio
@respx.mock
async def test_google_oauth_callback(async_client_with_db: AsyncClient, monkeypatch):
    state = "abc123"
    async def _verify_state(redis, st):
        return True

    monkeypatch.setattr("app.api.endpoints.oauth.verify_state", _verify_state)

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

    resp = await async_client_with_db.get(
        "/auth/oauth/google/callback",
        params={"code": "c", "state": state},
        cookies={"oauth_state": state},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
