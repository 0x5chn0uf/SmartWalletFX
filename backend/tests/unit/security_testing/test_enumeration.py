"""Unit tests for enumeration and generic-error helpers in security_testing."""

from __future__ import annotations

import time
from typing import Any

import pytest

from tests.utils.security_testing import (
    TimingAttackAssertionError,
    assert_generic_error_response,
    assert_no_user_enumeration,
)


class FakeResponse:
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self._detail = detail
        self.text = detail

    def json(self) -> dict[str, Any]:  # noqa: D401
        return {"detail": self._detail}


@pytest.mark.security
def test_generic_error_response_passes() -> None:
    resp = FakeResponse(401, "Invalid credentials")
    # Should not raise
    assert_generic_error_response(resp, 401, generic_substring="invalid")


@pytest.mark.security
def test_generic_error_response_fails_on_status() -> None:
    resp = FakeResponse(403, "Invalid credentials")
    with pytest.raises(TimingAttackAssertionError):
        assert_generic_error_response(resp, 401)


@pytest.mark.security
def test_no_user_enumeration_passes() -> None:
    """Auth func with constant time and generic error should pass."""

    valid_user = ("alice", "correct")

    def auth(username: str, password: str):
        # constant timing 1ms
        time.sleep(0.001)
        if (username, password) == valid_user:
            return {"token": "ok"}
        return FakeResponse(401, "Invalid credentials")

    invalids = [("alice", "wrong"), ("bob", "whatever")]
    assert_no_user_enumeration(
        auth_func=auth,
        valid_user=valid_user,
        invalid_users=invalids,
        iterations=10,
        threshold=0.5,  # loose threshold for unit speed
    )


@pytest.mark.security
def test_no_user_enumeration_detects_timing_diff() -> None:
    valid_user = ("alice", "ok")

    def auth(username: str, password: str):
        # Variable timing: fail fast for invalid users
        if (username, password) == valid_user:
            time.sleep(0.005)
            return {"token": "ok"}
        # shorter
        time.sleep(0.0001)
        return FakeResponse(401, "Invalid credentials")

    invalids = [("alice", "bad")]
    with pytest.raises(TimingAttackAssertionError):
        assert_no_user_enumeration(
            auth_func=auth,
            valid_user=valid_user,
            invalid_users=invalids,
            iterations=10,
            threshold=0.2,
        )
