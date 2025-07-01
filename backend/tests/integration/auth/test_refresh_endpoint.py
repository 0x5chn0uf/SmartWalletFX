import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import settings
from app.utils.jwt import JWTUtils

pytestmark = pytest.mark.usefixtures("client_with_db")


def _register_and_login(client: TestClient):
    username = "refreshuser"
    password = "Str0ngP@ssw0rd!"
    email = f"{username}@example.com"

    # Register
    res = client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert res.status_code == 201

    # Login – obtain tokens
    res = client.post(
        "/auth/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 200
    body = res.json()
    return body["access_token"], body["refresh_token"]


def test_refresh_success(client_with_db: TestClient):
    _, refresh_token = _register_and_login(client_with_db)

    res = client_with_db.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert res.status_code == 200
    body = res.json()

    # Same refresh token returned
    assert body["refresh_token"] == refresh_token
    assert body["access_token"]
    assert body["token_type"] == "bearer"

    # Verify roles claim present in new access token
    payload = jwt.get_unverified_claims(body["access_token"])
    assert "roles" in payload and payload["roles"]


def test_refresh_invalid_token(client_with_db: TestClient):
    invalid_token = JWTUtils.create_access_token("123")  # not a refresh token
    res = client_with_db.post("/auth/refresh", json={"refresh_token": invalid_token})
    assert res.status_code == 401
