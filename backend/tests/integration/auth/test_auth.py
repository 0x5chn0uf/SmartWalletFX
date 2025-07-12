from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from app.api.endpoints import auth as auth_ep
from app.core.config import settings
from app.domain.errors import InvalidCredentialsError
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService, WeakPasswordError
from app.utils.jwt import JWTUtils
from app.utils.rate_limiter import InMemoryRateLimiter, login_rate_limiter


@pytest.fixture(autouse=True)
async def _cleanup_auth_state():
    """Reset auth-related state between tests."""
    # Reset rate-limiter to avoid bleed-through from other tests
    login_rate_limiter.clear()

    # Clear cached JWT keys so downstream tests can reconfigure safely
    JWTUtils._get_sign_key.cache_clear()  # type: ignore[attr-defined]
    JWTUtils._get_verify_key.cache_clear()  # type: ignore[attr-defined]

    yield


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
@pytest.mark.asyncio
async def test_register_endpoint(
    test_app, async_client_with_db: AsyncClient, payload: dict, expected_status: int
) -> None:
    resp = await async_client_with_db.post("/auth/register", json=payload)
    assert resp.status_code == expected_status
    if expected_status == 201:
        body = resp.json()
        assert body["username"] == payload["username"]
        assert body["email"] == payload["email"]
        assert "hashed_password" not in body


@pytest.mark.asyncio
async def test_register_duplicate_email(
    test_app, async_client_with_db: AsyncClient
) -> None:
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

    assert (
        await async_client_with_db.post("/auth/register", json=payload1)
    ).status_code == 201
    dup_resp = await async_client_with_db.post("/auth/register", json=payload2)
    assert dup_resp.status_code == 409


@pytest.mark.asyncio
async def test_obtain_token_success(
    db_session, async_client_with_db: AsyncClient
) -> None:
    username = f"tokenuser-{uuid.uuid4().hex[:8]}"
    password = "Str0ng!pwd"
    email = f"token-{uuid.uuid4().hex[:8]}@ex.com"

    # Arrange – create user via service
    service = AuthService(db_session)
    await service.register(
        UserCreate(
            username=username,
            email=email,
            password=password,
        )
    )

    data = {"username": username, "password": password}
    resp = await async_client_with_db.post("/auth/token", data=data)
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert all(k in body for k in ("access_token", "refresh_token", "expires_in"))


@pytest.mark.asyncio
async def test_login_rate_limit(
    db_session, async_client_with_db: AsyncClient, mocker
) -> None:
    # Patch the global limiter for this test only to ensure full isolation
    mocker.patch(
        "app.api.dependencies.login_rate_limiter",
        new=InMemoryRateLimiter(
            settings.AUTH_RATE_LIMIT_ATTEMPTS,
            settings.AUTH_RATE_LIMIT_WINDOW_SECONDS,
        ),
    )

    username = f"rluser-{uuid.uuid4().hex[:8]}"
    email = f"rl-{uuid.uuid4().hex[:8]}@example.com"

    service = AuthService(db_session)
    await service.register(
        UserCreate(
            username=username,
            email=email,
            password="S3cur3!pwd",
        )
    )

    attempts = settings.AUTH_RATE_LIMIT_ATTEMPTS
    data = {"username": username, "password": "wrong-password"}

    # Exhaust allowed attempts (expect 401)
    for _ in range(attempts):
        r = await async_client_with_db.post("/auth/token", data=data)
        assert r.status_code == 401

    # Next attempt should be rate-limited
    r_final = await async_client_with_db.post("/auth/token", data=data)
    assert r_final.status_code == 429


@pytest.mark.asyncio
async def test_users_me_endpoint(async_client_with_db: AsyncClient, db_session) -> None:
    """/users/me should require auth and return current profile when token provided."""

    username = f"meuser-{uuid.uuid4().hex[:8]}"
    email = f"me-{uuid.uuid4().hex[:8]}@ex.com"

    # Register user & obtain token
    service = AuthService(db_session)
    await service.register(
        UserCreate(username=username, email=email, password="Str0ng!pwd")
    )

    token_resp = await async_client_with_db.post(
        "/auth/token", data={"username": username, "password": "Str0ng!pwd"}
    )
    assert token_resp.status_code == 200
    access_token = token_resp.json()["access_token"]

    # 1. Missing token → 401
    unauth = await async_client_with_db.get("/users/me")
    assert unauth.status_code == 401

    # 2. Valid token → 200 with expected fields
    headers = {"Authorization": f"Bearer {access_token}"}
    auth_resp = await async_client_with_db.get("/users/me", headers=headers)
    assert auth_resp.status_code == 200
    body = auth_resp.json()
    assert body["username"] == username
    assert body["email"] == email
    assert "hashed_password" not in body


class DummyAuthService:  # noqa: D101 – lightweight stub
    """Replacement AuthService that always raises expected errors."""

    def __init__(self, _session):
        pass

    async def register(self, payload: UserCreate):  # noqa: D401 – stub
        raise WeakPasswordError()

    async def authenticate(self, username: str, password: str):  # noqa: D401 – stub
        if username == "inactive":
            from app.domain.errors import InactiveUserError

            raise InactiveUserError()
        raise InvalidCredentialsError()


@pytest.fixture
def patched_auth_service(monkeypatch):
    """Patch *AuthService* used in auth endpoints with DummyAuthService."""
    original_service = auth_ep.AuthService
    monkeypatch.setattr(auth_ep, "AuthService", DummyAuthService)
    monkeypatch.setattr(auth_ep.AuthView, "_AuthView__auth_service", DummyAuthService, raising=False)
    yield
    monkeypatch.setattr(auth_ep, "AuthService", original_service)
    monkeypatch.setattr(auth_ep.AuthView, "_AuthView__auth_service", original_service, raising=False)


@pytest.mark.asyncio
async def test_token_invalid_credentials(
    test_app, patched_auth_service, async_client_with_db: AsyncClient
) -> None:
    data = {"username": "fake", "password": "wrong"}
    resp = await async_client_with_db.post("/auth/token", data=data)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_token_inactive_user(
    test_app, patched_auth_service, async_client_with_db: AsyncClient
) -> None:
    data = {"username": "inactive", "password": "any"}
    resp = await async_client_with_db.post("/auth/token", data=data)
    assert resp.status_code == 403  # Inactive users get 403, not 401


@pytest.mark.asyncio
async def test_register_weak_password_error(
    async_client_with_db: AsyncClient,
    monkeypatch,
) -> None:
    """AuthService.register raising WeakPasswordError → 400 Bad Request."""

    from app.api.endpoints import auth as auth_ep

    async def _raise_weak(self, payload):  # noqa: D401 – stub
        raise WeakPasswordError()

    # Patch *AuthService.register* only for this test
    monkeypatch.setattr(auth_ep.AuthService, "register", _raise_weak, raising=False)

    payload = {
        "username": "weakpw",
        "email": "weakpw@example.com",
        "password": "SupposedlyStr0ng1!",
    }
    resp = await async_client_with_db.post("/auth/register", json=payload)
    assert resp.status_code == 400
