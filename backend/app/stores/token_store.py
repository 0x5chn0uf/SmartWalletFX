from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token import Token
from app.schemas.token import TokenCreate


class TokenStore:
    @staticmethod
    async def create(db: AsyncSession, data: TokenCreate) -> Token:
        token = Token(
            address=data.address,
            symbol=data.symbol,
            name=data.name,
            decimals=data.decimals,
        )
        db.add(token)
        await db.commit()
        await db.refresh(token)
        return token
