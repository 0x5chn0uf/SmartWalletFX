from pydantic import BaseModel


class TokenPriceCreate(BaseModel):
    token_id: int
    price_usd: float


class TokenPriceResponse(BaseModel):
    id: int
    token_id: int
    price_usd: float
