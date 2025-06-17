import pytest

from app.repositories.token_price_repository import TokenPriceRepository
from app.schemas.token_price import TokenPriceCreate


@pytest.mark.asyncio
async def test_token_price_store(db_session):
    price = await TokenPriceRepository(db_session).create(
        TokenPriceCreate(token_id=1, price_usd=1.23),
    )
    assert float(price.price_usd) == pytest.approx(1.23)
