from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token_balance import TokenBalance
from app.schemas.token_balance import TokenBalanceCreate


class TokenBalanceStore:
    @staticmethod
    async def create(
        db: AsyncSession, data: TokenBalanceCreate
    ) -> TokenBalance:
        balance = TokenBalance(
            token_id=data.token_id,
            wallet_id=data.wallet_id,
            balance=data.balance,
            balance_usd=data.balance_usd,
        )
        db.add(balance)
        await db.commit()
        await db.refresh(balance)
        return balance
