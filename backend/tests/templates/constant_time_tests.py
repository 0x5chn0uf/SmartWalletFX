from __future__ import annotations

"""Constant‐time security property tests.

These leverage helpers from `tests.utils.security_testing` to ensure critical
operations such as password verification execute in constant time irrespective
of credential correctness.
"""

import pytest

try:
    from tests.utils import security_testing as st
except ModuleNotFoundError:  # pragma: no cover
    from backend.tests.utils import security_testing as st

try:
    from app.utils.security import PasswordHasher
except ModuleNotFoundError:  # pragma: no cover
    from backend.app.utils.security import PasswordHasher

pytestmark = pytest.mark.property


# Prepare test data: create a hashed password once.
PLAINTEXT = "S3cur3P@ssw0rd!"
HASHED = PasswordHasher.hash_password(PLAINTEXT)


def _verify(pwd: str) -> None:  # pragma: no cover
    PasswordHasher.verify_password(pwd, HASHED)


def test_verify_password_constant_time() -> None:  # pragma: no cover
    """Password verification timing variance should stay within 100% coefficient."""

    st.assert_constant_time_operation(
        _verify,
        inputs=[PLAINTEXT, "invalidpassword"],
        variance_threshold=1.0,
        iterations=50,
    )
