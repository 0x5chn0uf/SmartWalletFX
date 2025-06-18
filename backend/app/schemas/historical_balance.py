import uuid
from datetime import datetime

from pydantic import BaseModel


class HistoricalBalanceCreate(BaseModel):
    wallet_id: uuid.UUID
    token_id: uuid.UUID
    balance: float
    balance_usd: float
    timestamp: datetime


class HistoricalBalanceResponse(BaseModel):
    id: uuid.UUID
    wallet_id: uuid.UUID
    token_id: uuid.UUID
    balance: float
    balance_usd: float
    timestamp: datetime
