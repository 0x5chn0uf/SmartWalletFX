"""Unit tests for the `jwt_tokens` Hypothesis strategy."""
from __future__ import annotations


from hypothesis import given

from tests.strategies import security as strat_mod


@given(tok=strat_mod.jwt_tokens())
def test_jwt_token_has_three_parts(tok: str) -> None:  # pragma: no cover
    parts = tok.split(".")
    assert len(parts) == 3, f"expected 3 parts, got {len(parts)}"
    header, payload, signature = parts
    assert header, "header part empty"
    assert payload, "payload part empty"
    assert signature == "signature", "signature placeholder mismatch"
