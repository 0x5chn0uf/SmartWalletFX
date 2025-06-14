from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.defi import DeFiAccountSnapshot
from app.usecase.defi_radiant_usecase import RadiantUsecase


@pytest.mark.asyncio
@patch(
    "app.usecase.defi_radiant_usecase.RadiantContractAdapter.async_get_user_data",
    new_callable=AsyncMock,
)
async def test_radiant_usecase_none(mock_async_get):
    """
    get_user_snapshot should return None
    if adapter returns None.
    """
    mock_async_get.return_value = None
    usecase = RadiantUsecase()
    result = await usecase.get_user_snapshot("0x123")
    assert result is None


@pytest.mark.asyncio
@patch(
    "app.usecase.defi_radiant_usecase.RadiantContractAdapter.async_get_user_data",
    new_callable=AsyncMock,
)
async def test_radiant_usecase_mapping(mock_async_get):
    """
    get_user_snapshot should map contract result
    to DeFiAccountSnapshot.
    """
    mock_async_get.return_value = {
        "reserves": [
            {
                "token_address": "0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                "symbol": "USDC",
                "decimals": 6,
                "supplied": 500_000_000,  # 500 USDC (6 decimals)
                "supplied_usd": 500.0,
                "used_as_collateral": True,
                "variable_borrowed": 0,
                "stable_borrowed": 0,
            },
            {
                "token_address": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
                "symbol": "ETH",
                "decimals": 18,
                "supplied": 0,
                "supplied_usd": 0.0,
                "used_as_collateral": False,
                "variable_borrowed": 100_000_000_000_000_000,  # 0.1 ETH
                "stable_borrowed": 0,
            },
        ],
        "health_factor": 2.5,
    }
    usecase = RadiantUsecase()
    snapshot = await usecase.get_user_snapshot(
        "0x48840F6D69c979Af278Bb8259e15408118709F3F"
    )
    assert isinstance(snapshot, DeFiAccountSnapshot)
    assert snapshot.user_address == "0x48840F6D69c979Af278Bb8259e15408118709F3F"
    assert len(snapshot.collaterals) == 1
    assert snapshot.collaterals[0].asset == "0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    assert snapshot.collaterals[0].amount == 500.0
    assert snapshot.collaterals[0].usd_value == 500.0
    assert len(snapshot.borrowings) == 1
    assert snapshot.borrowings[0].asset == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
    assert snapshot.borrowings[0].amount == 0.1
    assert snapshot.borrowings[0].usd_value == 0
    assert snapshot.health_scores[0].score == 2.5
