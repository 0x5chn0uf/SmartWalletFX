from __future__ import annotations

"""Hypothesis strategy helpers for DeFi related tests."""

__all__ = [
    "portfolio_snapshot_strategy",
]


def portfolio_snapshot_strategy():
    """Return a Hypothesis strategy for generating PortfolioSnapshot instances."""

    from hypothesis import strategies as st

    from app.domain.schemas.defi import PortfolioSnapshot

    return st.builds(
        PortfolioSnapshot,
        user_address=st.text(
            min_size=40, max_size=42, alphabet="0123456789abcdefABCDEF"
        ),
        timestamp=st.integers(min_value=1600000000, max_value=2000000000),
        total_collateral=st.floats(min_value=0.0, max_value=100000.0),
        total_borrowings=st.floats(min_value=0.0, max_value=100000.0),
        total_collateral_usd=st.floats(min_value=0.0, max_value=100000.0),
        total_borrowings_usd=st.floats(min_value=0.0, max_value=100000.0),
        aggregate_health_score=st.floats(min_value=0.0, max_value=2.0),
        aggregate_apy=st.floats(min_value=0.0, max_value=100.0),
        collaterals=st.lists(
            st.builds(
                dict,
                protocol=st.sampled_from(["AAVE", "COMPOUND", "RADIANT"]),
                asset=st.text(min_size=3, max_size=10),
                amount=st.floats(min_value=0.0, max_value=1000.0),
                usd_value=st.floats(min_value=0.0, max_value=10000.0),
            ),
            max_size=5,
        ),
        borrowings=st.lists(
            st.builds(
                dict,
                protocol=st.sampled_from(["AAVE", "COMPOUND", "RADIANT"]),
                asset=st.text(min_size=3, max_size=10),
                amount=st.floats(min_value=0.0, max_value=1000.0),
                usd_value=st.floats(min_value=0.0, max_value=10000.0),
                interest_rate=st.floats(min_value=0.0, max_value=50.0),
            ),
            max_size=5,
        ),
        staked_positions=st.lists(
            st.builds(
                dict,
                protocol=st.sampled_from(["AAVE", "COMPOUND", "RADIANT"]),
                asset=st.text(min_size=3, max_size=10),
                amount=st.floats(min_value=0.0, max_value=1000.0),
                usd_value=st.floats(min_value=0.0, max_value=10000.0),
                apy=st.floats(min_value=0.0, max_value=100.0),
            ),
            max_size=5,
        ),
        health_scores=st.lists(
            st.builds(
                dict,
                protocol=st.sampled_from(["AAVE", "COMPOUND", "RADIANT"]),
                score=st.floats(min_value=0.0, max_value=2.0),
                total_value=st.floats(min_value=0.0, max_value=10000.0),
            ),
            max_size=3,
        ),
        protocol_breakdown=st.dictionaries(
            st.text(min_size=3, max_size=10),
            st.dictionaries(
                st.text(min_size=3, max_size=10),
                st.floats(min_value=0.0, max_value=1000.0),
                max_size=3,
            ),
            max_size=3,
        ),
    )
