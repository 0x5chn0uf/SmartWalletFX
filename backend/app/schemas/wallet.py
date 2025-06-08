from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class WalletCreate(BaseModel):
    address: str = Field(..., description="EVM wallet address")
    name: Optional[str] = Field(None, description="Wallet name")


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
