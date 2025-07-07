"""
DeFi aggregate metrics schemas.

Pydantic schemas for DeFi position aggregation API responses.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class PositionSchema(BaseModel):
    """Schema for individual DeFi position."""

    protocol: str = Field(..., example="aave", description="DeFi protocol name")
    asset: str = Field(..., example="DAI", description="Asset/token name")
    amount: float = Field(..., description="Position amount in asset units")
    usd_value: float = Field(..., ge=0, description="Position value in USD")
    apy: Optional[float] = Field(None, ge=0, description="Annual percentage yield")

    class Config:
        json_schema_extra = {
            "example": {
                "protocol": "aave",
                "asset": "DAI",
                "amount": 1234.56,
                "usd_value": 1234.56,
                "apy": 0.045,
            }
        }


class AggregateMetricsSchema(BaseModel):
    """Schema for aggregated DeFi metrics across multiple protocols."""

    id: str = Field(..., description="Unique identifier")
    wallet_id: str = Field(
        ..., pattern=r"^0x[a-fA-F0-9]{40}$", description="Ethereum wallet address"
    )
    tvl: float = Field(..., ge=0, description="Total value locked across all positions")
    total_borrowings: float = Field(
        ..., ge=0, description="Total borrowings across all protocols"
    )
    aggregate_apy: Optional[float] = Field(
        None, ge=0, description="Weighted average APY across all positions"
    )
    as_of: datetime = Field(..., description="Timestamp of the aggregation")
    positions: List[PositionSchema] = Field(
        ..., description="List of individual positions"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "wallet_id": "0x742d35cc6634c0532925a3b8d4c9db96c4b4d8b6",
                "tvl": 8750.0,
                "total_borrowings": 5000.0,
                "aggregate_apy": 0.067,
                "as_of": "2024-01-15T10:30:00Z",
                "positions": [
                    {
                        "protocol": "aave",
                        "asset": "USDC",
                        "amount": 1000.0,
                        "usd_value": 1000.0,
                        "apy": 0.05,
                    }
                ],
            }
        }

    @field_validator("wallet_id")
    def lowercase_address(cls, v: str) -> str:
        """Convert wallet address to lowercase."""
        return v.lower()
