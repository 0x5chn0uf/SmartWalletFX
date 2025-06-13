import pytest

from app.usecase.defi_aave_usecase import AaveUsecase
from app.usecase.defi_compound_usecase import CompoundUsecase
from app.usecase.defi_radiant_usecase import RadiantUsecase


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


class _StubClient:
    def __init__(self, payload):
        self._payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def post(self, *args, **kwargs):
        return _Resp(self._payload)


@pytest.mark.asyncio
async def test_aave_usecase(monkeypatch):
    payload = {
        "data": {
            "userReserves": [
                {
                    "reserve": {
                        "symbol": "USDC",
                        "decimals": 6,
                        "liquidityRate": 0,
                        "variableBorrowRate": 0,
                    },
                    "scaledATokenBalance": 1000000,
                    "currentTotalDebt": 0,
                }
            ],
            "userAccountData": {
                "healthFactor": 1e18,
                "totalCollateralETH": 0,
                "totalDebtETH": 0,
            },
        }
    }
    monkeypatch.setattr(
        "httpx.AsyncClient", lambda *a, **k: _StubClient(payload)
    )
    usecase = AaveUsecase()
    snap = await usecase.get_user_snapshot("0xabc")
    assert snap and snap.collaterals[0].asset == "USDC"


@pytest.mark.asyncio
async def test_compound_usecase(monkeypatch):
    payload = {
        "data": {
            "account": {
                "id": "0xabc",
                "health": "1.5",
                "tokens": [
                    {
                        "symbol": "cUSDC",
                        "supplyBalanceUnderlying": 100,
                        "borrowBalanceUnderlying": 0,
                    }
                ],
            }
        }
    }
    monkeypatch.setattr(
        "httpx.AsyncClient", lambda *a, **k: _StubClient(payload)
    )
    usecase = CompoundUsecase()
    snap = await usecase.get_user_snapshot("0xabc")
    assert snap and snap.collaterals[0].amount == 100


@pytest.mark.asyncio
async def test_radiant_usecase(monkeypatch):
    payload = {
        "data": {
            "userReserves": [],
            "userAccountData": None,
        }
    }
    monkeypatch.setattr(
        "app.usecase.defi_radiant_usecase.RadiantContractAdapter.async_get_user_data",
        lambda *a, **k: None,
    )
    usecase = RadiantUsecase()
    snap = await usecase.get_user_snapshot("0xabc")
    assert snap is None
