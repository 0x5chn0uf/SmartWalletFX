import pytest


@pytest.mark.parametrize(
    "payload, expected_status",
    [
        (
            {"username": "dave", "email": "dave@example.com", "password": "Str0ng!pwd"},
            201,
        ),
        (  # weak password
            {"username": "weak", "email": "weak@example.com", "password": "weakpass"},
            422,
        ),
    ],
)
def test_register_endpoint(client, payload, expected_status):
    response = client.post("/auth/register", json=payload)
    assert response.status_code == expected_status
    if expected_status == 201:
        body = response.json()
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
    resp_dup = client.post("/auth/register", json=payload2)
    assert resp_dup.status_code == 409
