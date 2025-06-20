from __future__ import annotations

"""Unit tests for `safe_sql_strings` strategy."""

from hypothesis import given

from tests.strategies import security as strat_mod


@given(sql=strat_mod.safe_sql_strings())
def test_sql_statement_is_simple(sql: str) -> None:  # pragma: no cover
    # Ensure ends with semicolon and contains no dangerous keywords.
    assert sql.endswith(";"), "SQL statement must end with semicolon"
    forbidden = {"DROP", "DELETE", "TRUNCATE", "ALTER"}
    upper_sql = sql.upper()
    for kw in forbidden:
        assert kw not in upper_sql, f"dangerous keyword {kw} present"
