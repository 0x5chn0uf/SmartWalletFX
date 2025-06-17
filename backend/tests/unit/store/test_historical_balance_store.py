import pytest

from app.repositories.historical_balance_repository import (
    HistoricalBalanceRepository,
)
from app.repositories.token_repository import TokenRepository
from app.schemas.historical_balance import HistoricalBalanceCreate
from app.schemas.token import TokenCreate


@pytest.mark.asyncio
async def test_historical_balance_store_create(db_session):
    token = await TokenRepository(db_session).create(
        TokenCreate(
            address="0xHis",
            symbol="HIS",
            name="Historical",
            decimals=18,
        ),
    )

    hist = await HistoricalBalanceRepository(db_session).create(
        HistoricalBalanceCreate(
            wallet_id=1,
            token_id=token.id,
            balance=50.0,
            balance_usd=50.0,
            timestamp=123,
        ),
    )
    assert hist.balance_usd == 50.0
