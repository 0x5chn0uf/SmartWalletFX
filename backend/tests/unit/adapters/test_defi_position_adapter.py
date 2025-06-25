import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.adapters.defi_position import DeFiPositionAdapter


@pytest.fixture
def adapter():
    return DeFiPositionAdapter()


# Helper class for creating mock snapshot objects
class MockAsset:
    def __init__(self, asset, amount, usd_value, apy):
        self.asset = asset
        self.amount = amount
        self.usd_value = usd_value
        self.apy = apy


class MockSnapshot:
    def __init__(self, supplies=None, borrows=None):
        self.supplies = supplies or []
        self.borrows = borrows or []


# --- Core tests ---
@pytest.mark.asyncio
async def test_fetch_positions_success(adapter):
    with patch("app.adapters.defi_position.AaveContractAdapter") as mock_aave, patch(
        "app.adapters.defi_position.CompoundContractAdapter"
    ) as mock_compound, patch(
        "app.adapters.defi_position.RadiantContractAdapter"
    ) as mock_radiant:
        # Mock snapshots with proper objects
        aave_snapshot = MockSnapshot(
            supplies=[MockAsset("USDC", 1000, 1000, 0.05)],
            borrows=[MockAsset("DAI", 500, 500, 0.08)],
        )
        compound_snapshot = MockSnapshot(supplies=[], borrows=[])

        mock_aave.return_value.get_user_snapshot = AsyncMock(return_value=aave_snapshot)
        mock_compound.return_value.get_user_snapshot = AsyncMock(
            return_value=compound_snapshot
        )
        mock_radiant.return_value.get_user_snapshot = AsyncMock(return_value=None)

        positions = await adapter.fetch_positions("0x1234567890abcdef")
        assert any(p["protocol"] == "aave" for p in positions)
        assert any(p["type"] == "supply" for p in positions)
        assert any(p["type"] == "borrow" for p in positions)


@pytest.mark.asyncio
async def test_fetch_positions_handles_exceptions(adapter):
    with patch("app.adapters.defi_position.AaveContractAdapter") as mock_aave, patch(
        "app.adapters.defi_position.CompoundContractAdapter"
    ) as mock_compound, patch(
        "app.adapters.defi_position.RadiantContractAdapter"
    ) as mock_radiant:
        mock_aave.return_value.get_user_snapshot = AsyncMock(
            side_effect=Exception("fail")
        )
        mock_compound.return_value.get_user_snapshot = AsyncMock(return_value=None)
        mock_radiant.return_value.get_user_snapshot = AsyncMock(return_value=None)
        positions = await adapter.fetch_positions("0x1234567890abcdef")
        assert positions == []


@pytest.mark.asyncio
async def test_fetch_aave_positions(adapter):
    with patch("app.adapters.defi_position.AaveContractAdapter") as mock_aave:
        aave_snapshot = MockSnapshot(
            supplies=[MockAsset("USDC", 1000, 1000, 0.05)],
            borrows=[MockAsset("DAI", 500, 500, 0.08)],
        )
        mock_aave.return_value.get_user_snapshot = AsyncMock(return_value=aave_snapshot)
        result = await adapter._fetch_aave_positions("0x1234567890abcdef")
        assert len(result) == 2
        assert result[0]["protocol"] == "aave"
        assert result[0]["type"] == "supply"
        assert result[1]["type"] == "borrow"


@pytest.mark.asyncio
async def test_fetch_aave_positions_handles_exception(adapter):
    with patch("app.adapters.defi_position.AaveContractAdapter") as mock_aave:
        mock_aave.return_value.get_user_snapshot = AsyncMock(
            side_effect=Exception("fail")
        )
        result = await adapter._fetch_aave_positions("0x1234567890abcdef")
        assert result == []


@pytest.mark.asyncio
async def test_fetch_compound_positions(adapter):
    with patch("app.adapters.defi_position.CompoundContractAdapter") as mock_compound:
        compound_snapshot = MockSnapshot(
            supplies=[MockAsset("ETH", 2, 4000, 0.03)], borrows=[]
        )
        mock_compound.return_value.get_user_snapshot = AsyncMock(
            return_value=compound_snapshot
        )
        result = await adapter._fetch_compound_positions("0x1234567890abcdef")
        assert len(result) == 1
        assert result[0]["protocol"] == "compound"
        assert result[0]["type"] == "supply"


@pytest.mark.asyncio
async def test_fetch_compound_positions_handles_exception(adapter):
    with patch("app.adapters.defi_position.CompoundContractAdapter") as mock_compound:
        mock_compound.return_value.get_user_snapshot = AsyncMock(
            side_effect=Exception("fail")
        )
        result = await adapter._fetch_compound_positions("0x1234567890abcdef")
        assert result == []


@pytest.mark.asyncio
async def test_fetch_radiant_positions(adapter):
    with patch("app.adapters.defi_position.RadiantContractAdapter") as mock_radiant:
        radiant_snapshot = MockSnapshot(
            supplies=[], borrows=[MockAsset("USDT", 100, 100, 0.02)]
        )
        mock_radiant.return_value.get_user_snapshot = AsyncMock(
            return_value=radiant_snapshot
        )
        result = await adapter._fetch_radiant_positions("0x1234567890abcdef")
        assert len(result) == 1
        assert result[0]["protocol"] == "radiant"
        assert result[0]["type"] == "borrow"


@pytest.mark.asyncio
async def test_fetch_radiant_positions_handles_exception(adapter):
    with patch("app.adapters.defi_position.RadiantContractAdapter") as mock_radiant:
        mock_radiant.return_value.get_user_snapshot = AsyncMock(
            side_effect=Exception("fail")
        )
        result = await adapter._fetch_radiant_positions("0x1234567890abcdef")
        assert result == []


def test_calculate_aggregate_metrics_basic(adapter):
    positions = [
        {
            "protocol": "aave",
            "asset": "USDC",
            "amount": 1000,
            "usd_value": 1000,
            "apy": 0.05,
            "type": "supply",
        },
        {
            "protocol": "compound",
            "asset": "ETH",
            "amount": 2,
            "usd_value": 4000,
            "apy": 0.03,
            "type": "supply",
        },
        {
            "protocol": "radiant",
            "asset": "USDT",
            "amount": 100,
            "usd_value": 100,
            "apy": 0.02,
            "type": "borrow",
        },
    ]
    metrics = adapter.calculate_aggregate_metrics(positions)
    assert metrics["tvl"] == 5000.0
    assert metrics["total_borrowings"] == 100.0
    # Weighted average: (1000 * 0.05 + 4000 * 0.03) / (1000 + 4000) = 0.034
    assert abs(metrics["aggregate_apy"] - 0.034) < 0.001
    assert metrics["positions"] == positions


def test_calculate_aggregate_metrics_empty(adapter):
    metrics = adapter.calculate_aggregate_metrics([])
    assert metrics["tvl"] == 0.0
    assert metrics["total_borrowings"] == 0.0
    assert metrics["aggregate_apy"] is None
    assert metrics["positions"] == []


def test_calculate_aggregate_metrics_only_borrow(adapter):
    positions = [
        {
            "protocol": "radiant",
            "asset": "USDT",
            "amount": 100,
            "usd_value": 100,
            "apy": 0.02,
            "type": "borrow",
        },
    ]
    metrics = adapter.calculate_aggregate_metrics(positions)
    assert metrics["tvl"] == 0.0
    assert metrics["total_borrowings"] == 100.0
    assert metrics["aggregate_apy"] is None


# --- Additional tests for 100% coverage ---
def test_init_covers_logger():
    adapter = DeFiPositionAdapter()
    assert isinstance(adapter.logger, logging.Logger)


@pytest.mark.asyncio
async def test_fetch_positions_logs_exception(monkeypatch):
    adapter = DeFiPositionAdapter()

    async def fail(*a, **kw):
        raise Exception("fail")

    adapter._fetch_aave_positions = fail
    adapter._fetch_compound_positions = fail
    adapter._fetch_radiant_positions = fail
    logs = []
    adapter.logger.error = lambda msg: logs.append(msg)
    result = await adapter.fetch_positions("0x123")
    assert result == []
    assert any("Error fetching DeFi positions" in m for m in logs)


@pytest.mark.asyncio
async def test_fetch_positions_logs_protocol_exception(monkeypatch):
    adapter = DeFiPositionAdapter()

    async def fail(*a, **kw):
        raise Exception("fail")

    async def ok(*a, **kw):
        return [{"protocol": "aave", "type": "supply", "usd_value": 1, "apy": 0.1}]

    adapter._fetch_aave_positions = ok
    adapter._fetch_compound_positions = fail
    adapter._fetch_radiant_positions = ok
    logs = []
    adapter.logger.warning = lambda msg: logs.append(msg)
    result = await adapter.fetch_positions("0x123")
    assert any(p["protocol"] == "aave" for p in result)
    assert any("Error fetching positions" in m for m in logs)


@pytest.mark.asyncio
async def test_fetch_aave_positions_supplies_borrows_none(monkeypatch):
    adapter = DeFiPositionAdapter()
    snapshot = MockSnapshot(supplies=None, borrows=None)
    with patch("app.adapters.defi_position.AaveContractAdapter") as mock_aave:
        mock_aave.return_value.get_user_snapshot = AsyncMock(return_value=snapshot)
        result = await adapter._fetch_aave_positions("0x123")
        assert result == []


@pytest.mark.asyncio
async def test_fetch_compound_positions_supplies_borrows_none(monkeypatch):
    adapter = DeFiPositionAdapter()
    snapshot = MockSnapshot(supplies=None, borrows=None)
    with patch("app.adapters.defi_position.CompoundContractAdapter") as mock_compound:
        mock_compound.return_value.get_user_snapshot = AsyncMock(return_value=snapshot)
        result = await adapter._fetch_compound_positions("0x123")
        assert result == []


@pytest.mark.asyncio
async def test_fetch_radiant_positions_supplies_borrows_none(monkeypatch):
    adapter = DeFiPositionAdapter()
    snapshot = MockSnapshot(supplies=None, borrows=None)
    with patch("app.adapters.defi_position.RadiantContractAdapter") as mock_radiant:
        mock_radiant.return_value.get_user_snapshot = AsyncMock(return_value=snapshot)
        result = await adapter._fetch_radiant_positions("0x123")
        assert result == []


@pytest.mark.asyncio
async def test_fetch_aave_positions_logs(monkeypatch):
    adapter = DeFiPositionAdapter()
    with patch("app.adapters.defi_position.AaveContractAdapter") as mock_aave:
        mock_aave.return_value.get_user_snapshot = AsyncMock(
            side_effect=Exception("fail")
        )
        logs = []
        adapter.logger.error = lambda msg: logs.append(msg)
        result = await adapter._fetch_aave_positions("0x123")
        assert result == []
        assert any("Error fetching Aave positions" in m for m in logs)


@pytest.mark.asyncio
async def test_fetch_compound_positions_logs(monkeypatch):
    adapter = DeFiPositionAdapter()
    with patch("app.adapters.defi_position.CompoundContractAdapter") as mock_compound:
        mock_compound.return_value.get_user_snapshot = AsyncMock(
            side_effect=Exception("fail")
        )
        logs = []
        adapter.logger.error = lambda msg: logs.append(msg)
        result = await adapter._fetch_compound_positions("0x123")
        assert result == []
        assert any("Error fetching Compound positions" in m for m in logs)


@pytest.mark.asyncio
async def test_fetch_radiant_positions_logs(monkeypatch):
    adapter = DeFiPositionAdapter()
    with patch("app.adapters.defi_position.RadiantContractAdapter") as mock_radiant:
        mock_radiant.return_value.get_user_snapshot = AsyncMock(
            side_effect=Exception("fail")
        )
        logs = []
        adapter.logger.error = lambda msg: logs.append(msg)
        result = await adapter._fetch_radiant_positions("0x123")
        assert result == []
        assert any("Error fetching Radiant positions" in m for m in logs)


def test_calculate_aggregate_metrics_weird_inputs(adapter):
    # Position with missing keys
    positions = [
        {"protocol": "aave", "type": "supply"},  # Missing usd_value, apy
        {"protocol": "compound", "type": "borrow", "usd_value": 100},  # Missing apy
    ]
    metrics = adapter.calculate_aggregate_metrics(positions)
    assert metrics["tvl"] == 0.0  # Missing usd_value defaults to 0
    assert metrics["total_borrowings"] == 100.0
    assert metrics["aggregate_apy"] is None  # No valid APY values

    # Position with None values
    positions = [
        {"protocol": "aave", "type": "supply", "usd_value": None, "apy": None},
    ]
    metrics = adapter.calculate_aggregate_metrics(positions)
    assert metrics["tvl"] == 0.0
    assert metrics["aggregate_apy"] is None


@pytest.mark.asyncio
async def test_fetch_aave_positions_full(monkeypatch):
    adapter = DeFiPositionAdapter()

    aave_snapshot = MockSnapshot(
        supplies=[MockAsset("USDC", 1000, 1000, 0.05)],
        borrows=[MockAsset("DAI", 500, 500, 0.08)],
    )

    with patch("app.adapters.defi_position.AaveContractAdapter") as mock_aave:
        mock_aave.return_value.get_user_snapshot = AsyncMock(return_value=aave_snapshot)
        result = await adapter._fetch_aave_positions("0x123")
        assert len(result) == 2
        assert result[0]["asset"] == "USDC"
        assert result[1]["asset"] == "DAI"


@pytest.mark.asyncio
async def test_fetch_compound_positions_full(monkeypatch):
    adapter = DeFiPositionAdapter()

    compound_snapshot = MockSnapshot(
        supplies=[MockAsset("ETH", 2, 4000, 0.03)],
        borrows=[MockAsset("USDC", 100, 100, 0.02)],
    )

    with patch("app.adapters.defi_position.CompoundContractAdapter") as mock_compound:
        mock_compound.return_value.get_user_snapshot = AsyncMock(
            return_value=compound_snapshot
        )
        result = await adapter._fetch_compound_positions("0x123")
        assert len(result) == 2
        assert result[0]["asset"] == "ETH"
        assert result[1]["asset"] == "USDC"


@pytest.mark.asyncio
async def test_fetch_radiant_positions_full(monkeypatch):
    adapter = DeFiPositionAdapter()

    radiant_snapshot = MockSnapshot(
        supplies=[MockAsset("WBTC", 1, 30000, 0.01)],
        borrows=[MockAsset("USDT", 100, 100, 0.02)],
    )

    with patch("app.adapters.defi_position.RadiantContractAdapter") as mock_radiant:
        mock_radiant.return_value.get_user_snapshot = AsyncMock(
            return_value=radiant_snapshot
        )
        result = await adapter._fetch_radiant_positions("0x123")
        assert len(result) == 2
        assert result[0]["asset"] == "WBTC"
        assert result[1]["asset"] == "USDT"
