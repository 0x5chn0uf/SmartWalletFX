# Security Testing Framework

This guide explains how to use the in-house _Security Test Framework_ (STF) added in Subtask 4.14. The STF lets any engineer verify that new authentication / security-critical code is resistant to side-channel leaks such as timing attacks and user enumeration.

---

## Why we need it

- Timing attacks can reveal information about credentials and secret keys even when output messages look identical.
- Developers often forget to keep error responses generic—leading to user-enumeration bugs.
- Manual inspection is unreliable; we need fast, repeatable, automated checks in CI.

---

## Quick-start

```python
from tests.utils.security_testing import (
    assert_constant_time_operation,
    assert_timing_attack_resistant,
    assert_no_user_enumeration,
)

# 1️⃣  Constant-time verification
assert_constant_time_operation(my_hash_compare, inputs=[b"a", b"bigger"], variance_threshold=0.05)

# 2️⃣  Timing attack detection
assert_timing_attack_resistant(
    login_func,
    valid_input=("alice", "secret"),
    invalid_inputs=[("alice", "bad"), ("bob", "whatever")],
)

# 3️⃣  User-enumeration guard (timing *and* error-message checks)
assert_no_user_enumeration(
    auth_func=login_func,
    valid_user=("alice", "secret"),
    invalid_users=[("alice", "wrong"), ("nosuch", "pw")],
)
```

All helpers raise `TimingAttackAssertionError` when a vulnerability is detected; tests therefore **fail** automatically in CI.

---

## Helper reference

| Helper                           | Purpose                                                                                              |
| -------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `measure_operation_timing`       | Low-level utility returning a list of nanosecond timings for a callable. Sync & async supported.     |
| `assert_constant_time_operation` | Fails when coefficient-of-variation of collected timings exceeds `variance_threshold` (default 5 %). |
| `assert_timing_attack_resistant` | Compares mean timing of _valid_ vs _invalid_ inputs; fails if ratio > `threshold` (default 10 %).    |
| `assert_generic_error_response`  | Ensures an HTTP-like response is generic (status + error text).                                      |
| `assert_no_user_enumeration`     | Combines timing analysis & generic-error check across credential variants.                           |
| `TimingAttackAssertionError`     | Raised by all STF helpers on security violations.                                                    |

---

## Running only security tests

```bash
pytest -m security  # from /backend
```

The CI workflow (`ci-cd.yml`) runs this subset in a dedicated **security-tests** job—fast feedback without waiting for the full suite.

---

## Configuration knobs

| Environment variable         | Description                                                  | Default |
| ---------------------------- | ------------------------------------------------------------ | ------- |
| `SEC_TEST_VARIANCE_FACTOR`   | Override global variance/thresholds in flaky CI environments | `0.05`  |
| `PYTEST_SECURITY_ITERATIONS` | How many timing iterations to run per input                  | `100`   |

Helpers also accept per-call keyword overrides when more control is needed.

---

## Extending STF

- Add new assertion helpers to `backend/tests/utils/security_testing.py`.
- Provide thorough unit-tests under `backend/tests/unit/security_testing/`.
- Document new helpers in this file.
