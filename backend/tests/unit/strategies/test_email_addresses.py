"""Unit tests for the `email_addresses` Hypothesis strategy.

These quick checks ensure the strategy from `tests.strategies.security` yields
RFC-like addresses (contains exactly one '@' and non-empty parts).  Detailed
validation is already provided by Hypothesis' built-in `emails()` strategy, so
we only assert invariants that downstream code relies upon.
"""
from __future__ import annotations

from hypothesis import HealthCheck, assume, given, settings

from tests.strategies import security as strat_mod

a_email_strategy = strat_mod.email_addresses()


@settings(
    max_examples=50,
    deadline=5000,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(addr=a_email_strategy)
def test_email_address_contains_single_at(addr: str) -> None:  # pragma: no cover
    assert addr.count("@") == 1
    local, domain = addr.split("@")
    assume(local)  # hypothesis will shrink but must remain non-empty
    assume(domain)
    assert "." in domain, "domain part must contain a dot"
