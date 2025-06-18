import uuid
from typing import Optional

from pydantic import BaseModel


class TokenCreate(BaseModel):
    address: str
    symbol: str
    name: str
    decimals: Optional[int] = 18


class TokenResponse(BaseModel):
    """
    Standard API response representation of an on-chain token.
    """

    id: uuid.UUID
    address: str
    symbol: str
    name: str
    decimals: Optional[int] = 18
