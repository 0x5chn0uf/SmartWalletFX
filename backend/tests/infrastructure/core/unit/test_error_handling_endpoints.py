import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.usefixtures("client")


def test_invalid_login_returns_structured_error(client: TestClient):
    """Ensure invalid credentials return JSON error payload with trace_id."""

    # Try to login with non-existent credentials without registering first
    bad_res = client.post(
        "/auth/token",
        data={"username": "nonexistent_user", "password": "wrong"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert bad_res.status_code == 401

    body = bad_res.json()
    assert {"detail", "code", "trace_id", "status_code"}.issubset(body.keys())
    assert body["status_code"] == 401
    assert body["code"] == "AUTH_FAILURE"
    assert body["trace_id"]  # non-empty
    # Header should match body trace_id
    assert bad_res.headers.get("X-Trace-Id") == body["trace_id"]


def test_no_plaintext_traceback_in_error_response(client: TestClient):
    """Ensure stack traces are not leaked in generic error responses (404/422 etc.)."""

    # Unknown path → 404 handled by global error handler
    resp = client.get("/nonexistent-path")
    assert resp.status_code == 404
    assert "Traceback (most recent call last)" not in resp.text
    assert "<module>" not in resp.text

    # Validation error on /auth/register (missing fields)
    bad = client.post("/auth/register", json={})
    assert bad.status_code == 422
    assert "Traceback" not in bad.text
