import pytest

from app.repositories.token_repository import TokenRepository
from app.schemas.token import TokenCreate


@pytest.mark.asyncio
async def test_token_repository_create(db_session):
    repo = TokenRepository(db_session)
    token = await repo.create(
        TokenCreate(
            address="0xToken",
            symbol="TKN",
            name="MockToken",
            decimals=18,
        )
    )
    assert token.symbol == "TKN"
    assert token.decimals == 18
