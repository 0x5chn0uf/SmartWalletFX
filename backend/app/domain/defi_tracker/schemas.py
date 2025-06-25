from __future__ import annotations

"""Pydantic schemas mirroring the DeFi Tracker domain entities.

These are *shared* between the API adapter layer and other infrastructure
(e.g. Celery tasks) but remain free of FastAPI-specific imports.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class PositionSchema(BaseModel):
    protocol: str = Field(..., example="aave")
    asset: str = Field(..., example="DAI")
    amount: float = Field(...)
    usd_value: float = Field(..., ge=0)
    apy: Optional[float] = Field(None, ge=0)

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "protocol": "aave",
                "asset": "DAI",
                "amount": 1234.56,
                "usd_value": 1234.56,
                "apy": 0.045,
            }
        }


class AggregateMetricsSchema(BaseModel):
    id: UUID
    wallet_id: str = Field(..., pattern=r"^0x[a-fA-F0-9]{40}$")
    tvl: float = Field(..., ge=0)
    total_borrowings: float = Field(..., ge=0)
    aggregate_apy: Optional[float] = Field(None, ge=0)
    as_of: datetime
    positions: List[PositionSchema]

    class Config:
        orm_mode = True

    @field_validator("wallet_id")
    def lowercase_address(cls, v: str) -> str:  # noqa: N805 – pydantic convention
        return v.lower()
