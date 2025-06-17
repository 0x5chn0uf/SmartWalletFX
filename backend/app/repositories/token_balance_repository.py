from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token_balance import TokenBalance
from app.schemas.token_balance import TokenBalanceCreate


class TokenBalanceRepository:
    """Repository for :class:`~app.models.token_balance.TokenBalance`."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: TokenBalanceCreate) -> TokenBalance:
        balance = TokenBalance(
            token_id=data.token_id,
            wallet_id=data.wallet_id,
            balance=data.balance,
            balance_usd=data.balance_usd,
        )
        self.db.add(balance)
        await self.db.commit()
        await self.db.refresh(balance)
        return balance
