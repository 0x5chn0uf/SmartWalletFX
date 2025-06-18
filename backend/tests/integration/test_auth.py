from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.api.endpoints import auth as auth_ep
from app.core.config import settings
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService, WeakPasswordError
from app.utils.jwt import JWTUtils
from app.utils.rate_limiter import login_rate_limiter


@pytest.mark.parametrize(
    "payload, expected_status",
    [
        (
            {
                "username": "dave",
                "email": "dave@example.com",
                "password": "Str0ng!pwd",
            },
            201,
        ),
        (
            # weak password – should be rejected by validation layer
            {
                "username": "weak",
                "email": "weak@example.com",
                "password": "weakpass",
            },
            422,
        ),
    ],
)
def test_register_endpoint(client, payload, expected_status):
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == expected_status
    if expected_status == 201:
        body = resp.json()
        assert body["username"] == payload["username"]
        assert body["email"] == payload["email"]
        assert "hashed_password" not in body


def test_register_duplicate_email(client):
    payload1 = {
        "username": "erin",
        "email": "erin@example.com",
        "password": "Str0ng!pwd",
    }
    payload2 = {
        "username": "erin2",
        "email": "erin@example.com",
        "password": "Str0ng!pwd",
    }

    assert client.post("/auth/register", json=payload1).status_code == 201
    dup_resp = client.post("/auth/register", json=payload2)
    assert dup_resp.status_code == 409


@pytest.mark.anyio
async def test_obtain_token_success(db_session, test_app):
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        # Arrange – create user via service
        service = AuthService(db_session)
        await service.register(
            UserCreate(
                username="tokenuser",
                email="token@ex.com",
                password="Str0ng!pwd",
            )
        )

        data = {"username": "tokenuser", "password": "Str0ng!pwd"}
        resp = await ac.post("/auth/token", data=data)
        assert resp.status_code == 200
        body = resp.json()
        assert body["token_type"] == "bearer"
        assert all(k in body for k in ("access_token", "refresh_token", "expires_in"))


@pytest.mark.anyio
async def test_login_rate_limit(db_session, test_app):
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        service = AuthService(db_session)
        await service.register(
            UserCreate(
                username="rluser",
                email="rl@example.com",
                password="S3cur3!pwd",
            )
        )

        attempts = settings.AUTH_RATE_LIMIT_ATTEMPTS
        data = {"username": "rluser", "password": "wrong-password"}

        # Exhaust allowed attempts (expect 401)
        for _ in range(attempts):
            r = await ac.post("/auth/token", data=data)
            assert r.status_code == 401

        # Next attempt should be rate-limited
        r_final = await ac.post("/auth/token", data=data)
        assert r_final.status_code == 429


@pytest.mark.anyio
@pytest.mark.xfail(reason="/users/me endpoint not yet implemented (Subtask 4.10)")
async def test_users_me_requires_auth(test_app):
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        resp = await ac.get("/users/me")
    assert resp.status_code == 401


class DummyAuthService:  # noqa: D101 – lightweight stub
    """Replacement AuthService that always raises expected errors."""

    def __init__(self, _session):
        pass

    async def register(self, payload: UserCreate):  # noqa: D401 – stub
        raise WeakPasswordError()

    async def authenticate(self, username: str, password: str):  # noqa: D401 – stub
        raise ValueError("invalid credentials")


@pytest.fixture
def patched_auth_service(monkeypatch):
    """Patch *AuthService* used in auth endpoints with DummyAuthService."""

    # Reset rate-limiter to avoid bleed-through from other tests
    login_rate_limiter.clear()

    # Clear cached JWT keys so downstream tests can reconfigure safely
    JWTUtils._get_sign_key.cache_clear()  # type: ignore[attr-defined]
    JWTUtils._get_verify_key.cache_clear()  # type: ignore[attr-defined]

    original_service = auth_ep.AuthService
    monkeypatch.setattr(auth_ep, "AuthService", DummyAuthService)
    yield
    monkeypatch.setattr(auth_ep, "AuthService", original_service)


def test_register_weak_password(client: TestClient, patched_auth_service):
    """Ensure /auth/register returns 400 when AuthService raises WeakPasswordError."""

    payload = {
        "username": "weak2",
        "email": "weak2@example.com",
        "password": "Str0ng!pwd",
    }
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 400
    assert resp.json()["detail"].startswith("Password does not meet")


@pytest.mark.anyio
async def test_token_invalid_credentials(test_app, patched_auth_service):
    """/auth/token should return 401 when authentication fails in AuthService."""

    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        resp = await ac.post("/auth/token", data={"username": "u", "password": "p"})
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid username or password"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Ensure in-memory rate-limiter is cleared between tests in this module."""

    login_rate_limiter.clear()
    yield
