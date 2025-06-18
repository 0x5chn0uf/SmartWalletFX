import uuid

from pydantic import BaseModel


class TokenPriceCreate(BaseModel):
    token_id: uuid.UUID
    price_usd: float


class TokenPriceResponse(BaseModel):
    id: uuid.UUID
    token_id: uuid.UUID
    price_usd: float
