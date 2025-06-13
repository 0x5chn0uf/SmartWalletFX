import pytest
import respx
from httpx import Response

from app.usecase.defi_compound_usecase import CompoundUsecase


@pytest.mark.asyncio
@respx.mock
async def test_compound_usecase_mapping():
    mock_response = {
        "data": {
            "account": {
                "id": "0x123",
                "health": "1.8",
                "tokens": [
                    {
                        "symbol": "USDC",
                        "supplyBalanceUnderlying": "500",
                        "borrowBalanceUnderlying": "0",
                    },
                    {
                        "symbol": "ETH",
                        "supplyBalanceUnderlying": "0",
                        "borrowBalanceUnderlying": "0.5",
                    },
                ],
            }
        }
    }
    respx.post(CompoundUsecase.SUBGRAPH_URL).mock(
        return_value=Response(200, json=mock_response)
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
@respx.mock
async def test_compound_usecase_not_found():
    respx.post(CompoundUsecase.SUBGRAPH_URL).mock(
        return_value=Response(200, json={"data": {"account": None}})
    )
    usecase = CompoundUsecase()
    snapshot = await usecase.get_user_snapshot("0xdead")
    assert snapshot is None
