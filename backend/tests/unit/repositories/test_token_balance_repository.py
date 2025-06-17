import pytest

from app.repositories.token_balance_repository import TokenBalanceRepository
from app.repositories.token_repository import TokenRepository
from app.schemas.token import TokenCreate
from app.schemas.token_balance import TokenBalanceCreate


@pytest.mark.asyncio
async def test_token_balance_repository_create(db_session):
    token = await TokenRepository(db_session).create(
        TokenCreate(
            address="0xTok",
            symbol="TOK",
            name="Token",
            decimals=18,
        )
    )
    balance = await TokenBalanceRepository(db_session).create(
        TokenBalanceCreate(
            token_id=token.id,
            wallet_id=1,
            balance=100.0,
            balance_usd=100.0,
        )
    )
    assert balance.balance_usd == 100.0
