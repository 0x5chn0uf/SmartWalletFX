import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.usefixtures("client")


def _register_user(
    client: TestClient, username: str, email: str, password: str
) -> None:
    res = client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert res.status_code == 201


def test_obtain_token_success(client: TestClient):
    username = "dana"
    password = "Sup3rStr0ng!!"
    _register_user(client, username, f"{username}@example.com", password)

    res = client.post(
        "/auth/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


def test_obtain_token_bad_credentials(client: TestClient):
    username = "edgar"
    password = "GoodPwd1!!"
    _register_user(client, username, f"{username}@example.com", password)

    res = client.post(
        "/auth/token",
        data={"username": username, "password": "wrongpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 401
