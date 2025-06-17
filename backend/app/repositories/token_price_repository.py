from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token_price import TokenPrice
from app.schemas.token_price import TokenPriceCreate


class TokenPriceRepository:
    """Repository for :class:`~app.models.token_price.TokenPrice`."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: TokenPriceCreate) -> TokenPrice:
        price = TokenPrice(
            token_id=data.token_id,
            price_usd=data.price_usd,
        )
        self.db.add(price)
        await self.db.commit()
        await self.db.refresh(price)
        return price
