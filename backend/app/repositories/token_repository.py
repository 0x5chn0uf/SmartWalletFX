from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token import Token
from app.schemas.token import TokenCreate


class TokenRepository:
    """Repository for :class:`~app.models.token.Token`."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: TokenCreate) -> Token:
        token = Token(
            address=data.address,
            symbol=data.symbol,
            name=data.name,
            decimals=data.decimals,
        )
        self.db.add(token)
        await self.db.commit()
        await self.db.refresh(token)
        return token
