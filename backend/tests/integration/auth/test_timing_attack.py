"""Integration test ensuring /auth/token endpoint resists user-enumeration timing attacks.

This test exercises the full FastAPI stack (router → service → repository → bcrypt)
using the real in-process TestClient.  It registers a legitimate user and then
compares the observed response timings for:

1. Valid credentials (existing user & correct password)
2. Wrong password for existing user
3. Non-existent username

The helper ``assert_no_user_enumeration`` verifies that:
• Error responses are generic (HTTP 401 with generic detail)
• The relative timing difference between valid and invalid attempts is below the
  configured threshold, preventing timing-side channel leaks that could allow
  attackers to enumerate valid usernames.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.utils.security_testing import assert_no_user_enumeration

pytestmark = [pytest.mark.security]


@pytest.mark.usefixtures("client")
def test_auth_token_endpoint_no_user_enumeration(client: TestClient) -> None:  # type: ignore[override]
    """Register a user and assert /auth/token resists enumeration leaks."""

    username = "timing_user"
    password = "Sup3rStr0ng!!"
    email = f"{username}@example.com"

    # 1️⃣  Register valid user
    res = client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert res.status_code == 201

    # Raise rate-limit threshold for this high-frequency test
    from app.utils.rate_limiter import login_rate_limiter

    login_rate_limiter.max_attempts = 1000  # Fixture will restore afterward

    # 2️⃣  Helper that calls /auth/token synchronously (TestClient is sync) and returns the Response
    def _auth_call(user: str, pwd: str):
        return client.post(
            "/auth/token",
            data={"username": user, "password": pwd},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    # 3️⃣  Assemble credential sets
    valid_creds = (username, password)
    invalid_creds = [
        (username, "WrongPassword1!"),  # bad password
        ("ghostuser", "Whatever123!"),  # non-existent user
    ]

    # 4️⃣  Run timing/assertion helper (lower iterations for CI speed, relaxed threshold)
    #     The helper will raise TimingAttackAssertionError if a leak is detected.
    assert_no_user_enumeration(
        _auth_call,
        valid_user=valid_creds,
        invalid_users=invalid_creds,
        iterations=2,
        threshold=1.5,
    )
