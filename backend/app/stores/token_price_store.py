from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token_price import TokenPrice
from app.schemas.token_price import TokenPriceCreate


class TokenPriceStore:
    @staticmethod
    async def create(db: AsyncSession, data: TokenPriceCreate) -> TokenPrice:
        price = TokenPrice(
            token_id=data.token_id,
            price_usd=data.price_usd,
        )
        db.add(price)
        await db.commit()
        await db.refresh(price)
        return price
