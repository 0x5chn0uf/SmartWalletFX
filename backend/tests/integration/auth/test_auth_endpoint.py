import pytest
from fastapi.testclient import TestClient

from app.api.endpoints import auth as auth_mod


@pytest.fixture
def client(test_app):
    # test_app fixture from conftest provides FastAPI app with DB overrides
    return TestClient(test_app)


def _setup_route(app):
    # Ensure router is included (might already in main but safeguard)
    if auth_mod.router not in app.router.routes:  # type: ignore[arg-type]
        app.include_router(auth_mod.router)


@pytest.mark.parametrize(
    "payload",
    [
        {
            "username": "alice",
            "email": "alice@example.com",
            "password": "StrongPass1!",
        }
    ],
)
def test_register_success(monkeypatch, client, payload):
    class DummyUser(dict):
        def __init__(self):
            super().__init__(
                id=1,
                username=payload["username"],
                email=payload["email"],
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z",
            )

        # allow attribute access for Pydantic
        def __getattr__(self, item):
            return self[item]

    async def _register(self, p):  # noqa: D401
        return DummyUser()

    monkeypatch.setattr(
        auth_mod, "AuthService", lambda db: type("S", (), {"register": _register})()
    )
    _setup_route(client.app)
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 201
    assert resp.json()["username"] == payload["username"]


@pytest.mark.parametrize(
    "exc_cls,status_code,detail",
    [
        (auth_mod.DuplicateError("username"), 409, "username already exists"),
        (
            auth_mod.WeakPasswordError(),
            400,
            "Password does not meet strength requirements",
        ),
    ],
)
def test_register_error_paths(monkeypatch, client, exc_cls, status_code, detail):
    async def _register(self, p):
        raise exc_cls

    monkeypatch.setattr(
        auth_mod, "AuthService", lambda db: type("S", (), {"register": _register})()
    )
    _setup_route(client.app)
    resp = client.post(
        "/auth/register",
        json={
            "username": "bob",
            "email": "bob@example.com",
            "password": "StrongPass1!",
        },
    )
    assert resp.status_code == status_code
    assert detail in resp.json()["detail"]
