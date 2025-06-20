import pytest
from fastapi.testclient import TestClient
from jose import jwt


@pytest.fixture
def user_payload():
    return {
        "username": "alice",
        "email": "alice@example.com",
        "password": "Str0ngPwd!",
    }


@pytest.mark.anyio
async def test_register_login_and_me(client: TestClient, user_payload):
    """Happy-path: register → login → protected `/users/me`."""

    # Register
    resp = client.post("/auth/register", json=user_payload)
    assert resp.status_code == 201, resp.text
    user_out = resp.json()
    assert user_out["username"] == user_payload["username"]
    assert user_out["email"] == user_payload["email"]
    assert "hashed_password" not in user_out, "Sensitive field leaked in response"

    # Login – OAuth2 Password flow expects form-encoded payload
    form = {
        "username": user_payload["username"],
        "password": user_payload["password"],
    }
    resp = client.post("/auth/token", data=form)
    assert resp.status_code == 200, resp.text
    tokens = resp.json()
    assert tokens["token_type"] == "bearer"
    assert "access_token" in tokens and tokens["access_token"]

    # Protected route
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = client.get("/users/me", headers=headers)
    assert resp.status_code == 200, resp.text
    me = resp.json()
    assert me["username"] == user_payload["username"]
    assert me["email"] == user_payload["email"]


def test_login_with_wrong_password(client: TestClient, user_payload):
    """Incorrect password should yield 401."""
    # Ensure user exists
    client.post("/auth/register", json=user_payload)

    bad_form = {"username": user_payload["username"], "password": "WrongPass1!"}
    resp = client.post("/auth/token", data=bad_form)
    assert resp.status_code == 401, resp.text


def test_protected_route_requires_token(client: TestClient):
    resp = client.get("/users/me")
    assert resp.status_code == 401, resp.text


def test_protected_route_rejects_invalid_token(client: TestClient):
    headers = {"Authorization": "Bearer invalid.token.here"}
    resp = client.get("/users/me", headers=headers)
    assert resp.status_code == 401, resp.text


@pytest.mark.anyio
async def test_access_token_contains_expected_claims(client: TestClient, user_payload):
    """Verify issued access token contains required claims."""

    client.post("/auth/register", json=user_payload)
    resp = client.post(
        "/auth/token",
        data={
            "username": user_payload["username"],
            "password": user_payload["password"],
        },
    )
    tokens = resp.json()

    payload = jwt.get_unverified_claims(tokens["access_token"])
    assert payload["sub"]  # subject present
    assert payload["type"] == "access"
    assert "jti" in payload
    assert "exp" in payload
