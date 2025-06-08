from datetime import datetime
from typing import Optional
import re

from pydantic import BaseModel, Field, validator


class WalletCreate(BaseModel):
    address: str = Field(..., description="EVM wallet address")
    name: Optional[str] = Field(None, description="Wallet name")

    @validator("address")
    def validate_address(cls, v):
        # Regex Ethereum address (0x suivi de 40 hex)
        if not re.match(r"^0x[a-fA-F0-9]{40}$", v):
            raise ValueError("Invalid Ethereum address format")
        return v


class WalletResponse(BaseModel):
    id: int
    address: str
    name: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool
    balance_usd: Optional[float]

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
                "name": "Example Wallet",
            }
        }
