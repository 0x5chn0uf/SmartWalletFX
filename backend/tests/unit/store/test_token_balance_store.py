import pytest

from app.schemas.token import TokenCreate
from app.schemas.token_balance import TokenBalanceCreate
from app.stores.token_balance_store import TokenBalanceStore
from app.stores.token_store import TokenStore


@pytest.mark.asyncio
async def test_token_balance_store_create(db_session):
    token = await TokenStore.create(
        db_session,
        TokenCreate(
            address="0xTok",
            symbol="TOK",
            name="Token",
            decimals=18,
        ),
    )
    balance = await TokenBalanceStore.create(
        db_session,
        TokenBalanceCreate(
            token_id=token.id,
            wallet_id=1,
            balance=100.0,
            balance_usd=100.0,
        ),
    )
    assert balance.balance_usd == 100.0
