import pytest

from app.schemas.historical_balance import HistoricalBalanceCreate
from app.schemas.token import TokenCreate
from app.stores.historical_balance_store import HistoricalBalanceStore
from app.stores.token_store import TokenStore


@pytest.mark.asyncio
async def test_historical_balance_store_create(db_session):
    token = await TokenStore.create(
        db_session,
        TokenCreate(
            address="0xHis",
            symbol="HIS",
            name="Historical",
            decimals=18,
        ),
    )

    hist = await HistoricalBalanceStore.create(
        db_session,
        HistoricalBalanceCreate(
            wallet_id=1,
            token_id=token.id,
            balance=50.0,
            balance_usd=50.0,
            timestamp=123,
        ),
    )
    assert hist.balance_usd == 50.0
