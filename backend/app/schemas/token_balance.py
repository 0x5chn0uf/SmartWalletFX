from pydantic import BaseModel


class TokenBalanceCreate(BaseModel):
    token_id: int
    wallet_id: int
    balance: float
    balance_usd: float


class TokenBalanceResponse(BaseModel):
    id: int
    token_id: int
    wallet_id: int
    balance: float
    balance_usd: float
