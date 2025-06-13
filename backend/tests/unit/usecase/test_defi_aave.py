import pytest
import respx
from httpx import Response

from app.usecase.defi_aave_usecase import AaveUsecase


@pytest.mark.asyncio
@respx.mock
async def test_aave_usecase_mapping():
    mock_response = {
        "data": {
            "userReserves": [
                {
                    "reserve": {
                        "symbol": "DAI",
                        "decimals": 18,
                        "liquidityRate": str(int(0.04 * 1e27)),
                        "variableBorrowRate": str(int(0.07 * 1e27)),
                    },
                    "scaledATokenBalance": str(int(1000 * 1e18)),
                    "currentTotalDebt": str(int(200 * 1e18)),
                }
            ],
            "userAccountData": {
                "healthFactor": str(int(2.1 * 1e18)),
                "totalCollateralETH": "10",
                "totalDebtETH": "2",
            },
        }
    }
    respx.post(AaveUsecase.SUBGRAPH_URL).mock(
        return_value=Response(200, json=mock_response)
    )
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
@respx.mock
async def test_aave_usecase_not_found():
    respx.post(AaveUsecase.SUBGRAPH_URL).mock(
        return_value=Response(
            200, json={"data": {"userReserves": [], "userAccountData": None}}
        )
    )
    usecase = AaveUsecase()
    snapshot = await usecase.get_user_snapshot("0xdead")
    assert snapshot is None
