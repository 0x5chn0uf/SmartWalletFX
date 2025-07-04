"""Unit tests for the `strong_passwords` Hypothesis strategy.

These tests intentionally fail until `strong_passwords` is fully implemented,
serving as the RED stage for the TDD cycle in Subtask 4.17.
"""
from __future__ import annotations


import string

from hypothesis import given

# Import the strategy module; depending on package discovery, fallback path without the
# `backend` prefix may be required when the root package is already `backend`.
from tests.strategies import security as strat_mod


@given(pwd=strat_mod.strong_passwords())
def test_password_meets_minimum_requirements(pwd: str) -> None:  # pragma: no cover
    """Every generated password should have at least 8 chars, a digit, and a symbol."""

    assert len(pwd) >= 8, "password too short (<8)"
    assert any(c.isdigit() for c in pwd), "password missing digit"
    symbol_set = set(string.punctuation)
    assert any(c in symbol_set for c in pwd), "password missing symbol"
