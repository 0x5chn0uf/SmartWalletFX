import re
import uuid
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class WalletCreate(BaseModel):
    """
    Pydantic schema for wallet creation input.
    Used for validating wallet creation requests.
    """

    address: str = Field(..., description="EVM wallet address")
    name: Optional[str] = Field(None, description="Wallet name")

    @field_validator("address")
    def validate_address(cls, v):
        """
        Validate the wallet address format.
        Args:
            v: Wallet address string.
        Returns:
            str: The validated address.
        Raises:
            ValueError: If the address format is invalid.
        """
        # Regex Ethereum address (0x suivi de 40 hex)
        if not re.match(r"^0x[a-fA-F0-9]{40}$", v):
            raise ValueError("Invalid Ethereum address format")
        return v


class WalletResponse(BaseModel):
    """
    Pydantic schema for wallet response output.
    Used for serializing wallet data in API responses.
    """

    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    address: str
    name: Optional[str]
    is_active: bool
    balance_usd: Optional[float]

    class Config:
        """
        Pydantic configuration for WalletResponse schema.
        """

        from_attributes = True
        json_schema_extra = {
            "example": {
                "address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
                "name": "Example Wallet",
            }
        }
