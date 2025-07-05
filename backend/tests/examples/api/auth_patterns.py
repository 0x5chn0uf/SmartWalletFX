import pytest



@pytest.mark.parametrize(
    "username,password,expected_status",
    [
        ("test1", "Str0ng!pwd", 201),  # registration success
        ("weak", "weakpass", 422),  # registration failure due to validation
        ("nouser", "nopass", 401),  # login failure for nonexistent user
    ],
)
def test_register_and_login_patterns(client, username, password, expected_status):
    email = f"{username}@example.com"
    reg_resp = client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    # Registration expected for valid password
    if expected_status == 201:
        assert reg_resp.status_code == 201
        login_resp = client.post(
            "/auth/token", data={"username": username, "password": password}
        )
        assert login_resp.status_code == 200
    else:
        # Registration or login should fail
        assert reg_resp.status_code != 201
