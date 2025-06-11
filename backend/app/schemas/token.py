from typing import Optional

from pydantic import BaseModel


class TokenCreate(BaseModel):
    address: str
    symbol: str
    name: str
    decimals: Optional[int] = 18


class TokenResponse(BaseModel):
    id: int
    address: str
    symbol: str
    name: str
    decimals: Optional[int] = 18
