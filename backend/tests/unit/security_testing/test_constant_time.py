"""Tests for assert_constant_time_operation (initial failing RED phase).

These tests use two toy functions:
    constant_func -> returns input after small fixed delay
    variable_func -> delay proportional to input length

assert_constant_time_operation should pass for constant_func and fail for variable_func.
Stub implementation currently raises NotImplementedError, so both tests expect failure.
"""

from __future__ import annotations

import math
import time

import pytest

from tests.utils.security_testing import (
    TimingAttackAssertionError,
    assert_constant_time_operation,
)

pytestmark = pytest.mark.nightly


def constant_func(value: str) -> None:
    # Sleep for fixed 1 ms to simulate constant-time operation
    time.sleep(0.001)


def variable_func(value: str) -> None:
    # Sleep proportional to input length (variable time)
    time.sleep(0.0001 * len(value))


@pytest.mark.security
def test_constant_time_passes() -> None:
    """assert_constant_time_operation should consider constant_func secure."""
    inputs = ["a", "bb", "ccc", "dddd"]
    # Should NOT raise
    assert_constant_time_operation(
        constant_func, inputs, iterations=30, variance_threshold=0.5
    )


@pytest.mark.security
def test_variable_time_fails() -> None:
    """assert_constant_time_operation should detect timing variance in variable_func."""
    inputs = ["a", "bb", "ccc", "dddd"]
    with pytest.raises(TimingAttackAssertionError):
        assert_constant_time_operation(variable_func, inputs, iterations=30)
