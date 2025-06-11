from datetime import datetime

from pydantic import BaseModel


class HistoricalBalanceCreate(BaseModel):
    wallet_id: int
    token_id: int
    balance: float
    balance_usd: float
    timestamp: datetime


class HistoricalBalanceResponse(BaseModel):
    id: int
    wallet_id: int
    token_id: int
    balance: float
    balance_usd: float
    timestamp: datetime
