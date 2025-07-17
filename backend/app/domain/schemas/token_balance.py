import uuid

from pydantic import BaseModel


class TokenBalanceCreate(BaseModel):
    token_id: uuid.UUID
    wallet_id: uuid.UUID
    balance: float
    balance_usd: float


class TokenBalanceResponse(BaseModel):
    id: uuid.UUID
    token_id: uuid.UUID
    wallet_id: uuid.UUID
    balance: float
    balance_usd: float
