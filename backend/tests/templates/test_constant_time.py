"""Constant‐time security property tests.

These leverage helpers from `tests.utils.security_testing` to ensure critical
operations such as password verification execute in constant time irrespective
of credential correctness.
"""
from __future__ import annotations

import pytest

from app.utils.security import PasswordHasher
from tests.utils import security_testing as st

pytestmark = pytest.mark.property


# Prepare test data: create a hashed password once.
PLAINTEXT = "S3cur3P@ssw0rd!"
HASHED = PasswordHasher.hash_password(PLAINTEXT)


def _verify(pwd: str) -> None:  # pragma: no cover
    PasswordHasher.verify_password(pwd, HASHED)


def test_verify_password_constant_time() -> None:  # pragma: no cover
    """Password verification timing variance should stay within 200% coefficient."""

    st.assert_constant_time_operation(
        _verify,
        inputs=[PLAINTEXT, "invalidpassword"],
        variance_threshold=2.0,
        iterations=20,
    )
