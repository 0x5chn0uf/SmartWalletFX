import pytest

from app.schemas.token_price import TokenPriceCreate
from app.stores.token_price_store import TokenPriceStore


@pytest.mark.asyncio
async def test_token_price_store(db_session):
    price = await TokenPriceStore.create(
        db_session,
        TokenPriceCreate(token_id=1, price_usd=1.23),
    )
    assert float(price.price_usd) == pytest.approx(1.23)
