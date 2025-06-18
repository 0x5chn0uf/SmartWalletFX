import pytest

from app.repositories.token_price_repository import TokenPriceRepository
from app.repositories.token_repository import TokenRepository
from app.schemas.token import TokenCreate
from app.schemas.token_price import TokenPriceCreate


@pytest.mark.asyncio
async def test_token_price_repository_create(db_session):
    token = await TokenRepository(db_session).create(
        TokenCreate(address="0xToken", symbol="TKN", name="MockToken", decimals=18)
    )

    price = await TokenPriceRepository(db_session).create(
        TokenPriceCreate(token_id=token.id, price_usd=1.23)
    )
    assert float(price.price_usd) == pytest.approx(1.23)
