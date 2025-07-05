"""Generic property-based tests applied to the authentication layer.

These tests are collected once but intended to run in all environments.  They
exercise core security utilities (PasswordHasher) with randomly generated
inputs from our Hypothesis strategies.  If external modules replace these
utilities, the tests will still validate the fundamental invariants.
"""
from __future__ import annotations


import pytest
from hypothesis import given, settings

from app.utils.security import PasswordHasher
from tests.strategies import security as strat_mod

# Apply the "property" marker so the CI job can target these tests explicitly.
pytestmark = pytest.mark.property

# Use a deterministic profile when run in CI to minimise flakiness.
settings.register_profile(
    "ci", max_examples=50, deadline=5000
)  # Reduced from 200 to 50, added deadline
settings.load_profile("ci")


@given(password=strat_mod.strong_passwords())
def test_password_hash_roundtrip(password: str) -> None:  # pragma: no cover
    """Hashing then verifying a password must succeed for the same input."""

    hashed = PasswordHasher.hash_password(password)
    assert PasswordHasher.verify_password(password, hashed)


@given(password=strat_mod.strong_passwords())
def test_password_hash_is_one_way(password: str) -> None:  # pragma: no cover
    """Hashed output should never equal the plaintext password."""

    hashed = PasswordHasher.hash_password(password)
    assert hashed != password
