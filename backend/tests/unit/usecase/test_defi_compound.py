import pytest
from app.schemas.defi import (
    Borrowing,
    Collateral,
    DeFiAccountSnapshot,
    HealthScore,
    ProtocolName,
)

from app.usecase.defi_compound_usecase import CompoundUsecase


@pytest.mark.asyncio
async def test_compound_usecase_mapping(monkeypatch):
    async def _fake_fetch(self, address: str):  # noqa: D401
        return DeFiAccountSnapshot(
            user_address=address,
            timestamp=0,
            collaterals=[
                Collateral(
                    protocol=ProtocolName.compound,
                    asset="USDC",
                    amount=500.0,
                    usd_value=500.0,
                )
            ],
            borrowings=[
                Borrowing(
                    protocol=ProtocolName.compound,
                    asset="ETH",
                    amount=0.5,
                    usd_value=0.5,
                    interest_rate=None,
                )
            ],
            staked_positions=[],
            health_scores=[
                HealthScore(protocol=ProtocolName.compound, score=1.8)
            ],
            total_apy=None,
        )

    monkeypatch.setattr(
        CompoundUsecase, "get_user_snapshot", _fake_fetch, raising=True
    )

    usecase = CompoundUsecase()
    snapshot = await usecase.get_user_snapshot("0x123")
    assert snapshot is not None
    assert snapshot.user_address == "0x123"
    assert len(snapshot.collaterals) == 1
    assert snapshot.collaterals[0].asset == "USDC"
    assert abs(snapshot.collaterals[0].amount - 500) < 1e-6
    assert len(snapshot.borrowings) == 1
    assert snapshot.borrowings[0].asset == "ETH"
    assert abs(snapshot.borrowings[0].amount - 0.5) < 1e-6
    assert len(snapshot.health_scores) == 1
    assert abs(snapshot.health_scores[0].score - 1.8) < 1e-6


@pytest.mark.asyncio
async def test_compound_usecase_not_found(monkeypatch):
    usecase = CompoundUsecase()
    snapshot = await usecase.get_user_snapshot("0xdead")
    assert snapshot is None
