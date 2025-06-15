"""Reusable Hypothesis strategies for property-based tests."""

from decimal import Decimal
from typing import Dict, List

from hypothesis import strategies as st

from app.schemas.defi import (
    Borrowing,
    Collateral,
    HealthScore,
    PortfolioSnapshot,
    ProtocolName,
    StakedPosition,
)

# Primitive strategies
address_str = st.from_regex(r"0x[a-fA-F0-9]{40}", fullmatch=True)
amount = st.decimals(min_value=Decimal("0"), max_value=Decimal("1000000"), places=2)
float_0_2 = st.floats(min_value=0, max_value=2, allow_nan=False, allow_infinity=False)

protocol = st.sampled_from(list(ProtocolName))
asset_symbol = st.text(min_size=3, max_size=6, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ")


@st.composite
def collateral_strategy(draw) -> Collateral:
    return Collateral(
        protocol=draw(protocol),
        asset=draw(asset_symbol),
        amount=float(draw(amount)),
        usd_value=float(draw(amount)),
    )


@st.composite
def borrowing_strategy(draw) -> Borrowing:
    return Borrowing(
        protocol=draw(protocol),
        asset=draw(asset_symbol),
        amount=float(draw(amount)),
        usd_value=float(draw(amount)),
        interest_rate=None,
    )


@st.composite
def staked_strategy(draw) -> StakedPosition:
    return StakedPosition(
        protocol=draw(protocol),
        asset=draw(asset_symbol),
        amount=float(draw(amount)),
        usd_value=float(draw(amount)),
        apy=None,
    )


@st.composite
def health_score_strategy(draw) -> HealthScore:
    return HealthScore(protocol=draw(protocol), score=draw(float_0_2))


@st.composite
def portfolio_snapshot_strategy(draw) -> PortfolioSnapshot:
    timestamp = draw(st.integers(min_value=1, max_value=2_000_000_000))
    collaterals: List[Collateral] = draw(st.lists(collateral_strategy(), max_size=5))
    borrowings: List[Borrowing] = draw(st.lists(borrowing_strategy(), max_size=5))
    staked = draw(st.lists(staked_strategy(), max_size=5))
    health_scores = draw(st.lists(health_score_strategy(), max_size=3))
    total_collateral = sum(c.amount for c in collaterals)
    total_borrowings = sum(b.amount for b in borrowings)
    aggregate_health = (
        float(sum(h.score for h in health_scores) / len(health_scores))
        if health_scores
        else 1.0
    )

    return PortfolioSnapshot(
        user_address=draw(address_str),
        timestamp=timestamp,
        total_collateral=total_collateral,
        total_borrowings=total_borrowings,
        total_collateral_usd=total_collateral,
        total_borrowings_usd=total_borrowings,
        aggregate_health_score=aggregate_health,
        aggregate_apy=None,
        collaterals=collaterals,
        borrowings=borrowings,
        staked_positions=staked,
        health_scores=health_scores,
        protocol_breakdown={},
    )
