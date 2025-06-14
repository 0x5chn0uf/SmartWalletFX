import pytest

from app.schemas.defi import (
    Borrowing,
    Collateral,
    DeFiAccountSnapshot,
    HealthScore,
    ProtocolName,
    StakedPosition,
)
from app.usecase.defi_aave_usecase import AaveUsecase


@pytest.mark.asyncio
async def test_aave_usecase_mapping(monkeypatch):
    """Validate snapshot structure without hitting network/web3."""

    async def _fake_fetch(self, address: str):  # noqa: D401
        return DeFiAccountSnapshot(
            user_address=address,
            timestamp=0,
            collaterals=[
                Collateral(
                    protocol=ProtocolName.aave,
                    asset="DAI",
                    amount=1000.0,
                    usd_value=1000.0,
                )
            ],
            borrowings=[
                Borrowing(
                    protocol=ProtocolName.aave,
                    asset="DAI",
                    amount=200.0,
                    usd_value=200.0,
                    interest_rate=0.07,
                )
            ],
            staked_positions=[
                StakedPosition(
                    protocol=ProtocolName.aave,
                    asset="stkAAVE",
                    amount=500.0,
                    usd_value=500.0,
                    apy=0.04,
                )
            ],
            health_scores=[HealthScore(protocol=ProtocolName.aave, score=2.1)],
            total_apy=None,
        )

    monkeypatch.setattr(AaveUsecase, "get_user_snapshot", _fake_fetch, raising=True)

    usecase = AaveUsecase()
    snapshot = await usecase.get_user_snapshot("0x123")
    assert snapshot is not None
    assert snapshot.user_address == "0x123"
    assert len(snapshot.collaterals) == 1
    assert snapshot.collaterals[0].asset == "DAI"
    assert abs(snapshot.collaterals[0].amount - 1000) < 1e-6
    assert len(snapshot.borrowings) == 1
    assert snapshot.borrowings[0].asset == "DAI"
    assert abs(snapshot.borrowings[0].amount - 200) < 1e-6
    assert snapshot.borrowings[0].interest_rate == 0.07
    assert len(snapshot.staked_positions) == 1
    assert snapshot.staked_positions[0].apy == 0.04
    assert len(snapshot.health_scores) == 1
    assert abs(snapshot.health_scores[0].score - 2.1) < 1e-6


@pytest.mark.asyncio
async def test_aave_usecase_not_found(monkeypatch):
    async def _fake_fetch(self, address: str):  # noqa: D401
        return None

    monkeypatch.setattr(AaveUsecase, "get_user_snapshot", _fake_fetch, raising=True)

    usecase = AaveUsecase()
    snapshot = await usecase.get_user_snapshot("0xdead")
    assert snapshot is None
