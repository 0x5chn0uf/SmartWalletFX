import uuid

import pytest

from app.repositories.token_repository import TokenRepository
from app.schemas.token import TokenCreate


@pytest.mark.asyncio
async def test_token_repository_create(db_session):
    repo = TokenRepository(db_session)
    address = f"0x{uuid.uuid4().hex[:40]}"
    token = await repo.create(
        TokenCreate(
            address=address,
            symbol="TKN",
            name="MockToken",
            decimals=18,
        )
    )
    assert token.symbol == "TKN"
    assert token.decimals == 18
