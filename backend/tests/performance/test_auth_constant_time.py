"""Cross-validate constant-time guarantees for password verification.

This test uses the Security Test Framework helper `assert_timing_attack_resistant`
to ensure timing difference between successful and failed password verification
remains below the acceptable threshold (default 10 %).
"""

from pathlib import Path

import pytest

from app.utils.security import PasswordHasher
from tests.utils.security_testing import assert_timing_attack_resistant

pytestmark = pytest.mark.performance


@pytest.mark.benchmark(group="auth-constant-time")
def test_password_verification_constant_time(tmp_path: Path):
    """PasswordHasher.verify_password should not leak timing information."""

    good_password = "PerfUserPassw0rd!"
    bad_passwords = ["wrongpass", "12345678", "differentPass1!"]

    hasher = PasswordHasher()
    hashed = hasher.hash_password(good_password)

    def _verify(pw: str):
        return hasher.verify_password(pw, hashed)

    # valid_input returns bool True; invalid inputs return bool False, but timing
    # variance between them should stay below 10 %
    assert_timing_attack_resistant(
        _verify,
        valid_input=good_password,
        invalid_inputs=bad_passwords,
        threshold=2.0,
        iterations=50,
    )
