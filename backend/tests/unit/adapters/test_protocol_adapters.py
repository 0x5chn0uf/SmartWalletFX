import pytest

from app.adapters.protocols.aave import AaveContractAdapter
from app.adapters.protocols.compound import CompoundContractAdapter
from app.adapters.protocols.radiant import RadiantContractAdapter
from app.schemas.defi import DeFiAccountSnapshot, Collateral, ProtocolName


@pytest.mark.asyncio
async def test_adapter_returns_snapshot(monkeypatch):
    adapter = AaveContractAdapter()

    dummy_snapshot = DeFiAccountSnapshot(  # minimal snapshot
        user_address="0xabc",
        timestamp=0,
        collaterals=[
            Collateral(protocol=ProtocolName.aave, asset="ETH", amount=1, usd_value=2000)
        ],
        borrowings=[],
        staked_positions=[],
        health_scores=[],
        total_apy=None,
    )

    async def _mock_usecase(self, address: str):  # noqa: D401 – test helper
        return dummy_snapshot

    # Patch underlying usecase called by adapter
    monkeypatch.setattr(
        "app.usecase.defi_aave_usecase.AaveUsecase.get_user_snapshot",
        _mock_usecase,
    )

    snapshot = await adapter.fetch_snapshot("0xabc")
    assert snapshot == dummy_snapshot


@pytest.mark.asyncio
async def test_compound_adapter_handles_none(monkeypatch):
    adapter = CompoundContractAdapter()

    async def _mock_usecase(self, address: str):  # noqa: D401
        return None

    monkeypatch.setattr(
        "app.usecase.defi_compound_usecase.CompoundUsecase.get_user_snapshot",
        _mock_usecase,
    )

    snapshot = await adapter.fetch_snapshot("0xabc")
    assert snapshot is None


@pytest.mark.asyncio
async def test_radiant_adapter(monkeypatch):
    adapter = RadiantContractAdapter()

    async def _mock_usecase(self, address: str):  # noqa: D401
        return None

    monkeypatch.setattr(
        "app.usecase.defi_radiant_usecase.RadiantUsecase.get_user_snapshot",
        _mock_usecase,
    )

    snapshot = await adapter.fetch_snapshot("0xabc")
    assert snapshot is None 