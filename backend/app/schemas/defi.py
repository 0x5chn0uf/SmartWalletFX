"""
Agnostic Pydantic models for multi-protocol DeFi
(Aave, Compound, Radiant, etc.)

These models provide a unified structure for representing DeFi user data
(collateral, borrowing, staked position, health score, etc.) across multiple
protocols. They are used for:

- **Data aggregation**: Abstracting protocol-specific data (Aave, Compound,
  Radiant, etc.) into a common format for backend processing.
- **Persistence**: Serving as the schema for local storage (database), enabling
  efficient querying, aggregation, and historical tracking.
- **Validation**: Ensuring data integrity when ingesting or exposing DeFi data
  via API endpoints.

## Model Overview
- `ProtocolName`: Enum for supported DeFi protocols.
- `Collateral`, `Borrowing`, `StakedPosition`, `HealthScore`: Entities
  representing user positions, normalized across protocols.
- `DeFiAccountSnapshot`: Aggregates all user data at a given timestamp, for a
  given wallet/user.

## Protocol Mapping
- See `docs/defi_api_mapping.md` for the mapping between protocol-specific
  fields and these models.
- Data is typically fetched via smart contract calls, then
  mapped to these models for storage and API use.

## Usage Example
- When fetching user data from Aave, Compound, or Radiant, map the results to
  these models before persisting or returning via API.
- These models can be extended to support new protocols or additional fields as
  needed.
"""
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class ProtocolName(str, Enum):
    aave = "AAVE"
    compound = "COMPOUND"
    radiant = "RADIANT"
    other = "OTHER"


class Collateral(BaseModel):
    protocol: ProtocolName
    asset: str
    amount: float
    usd_value: float


class Borrowing(BaseModel):
    protocol: ProtocolName
    asset: str
    amount: float
    usd_value: float
    interest_rate: Optional[float]


class StakedPosition(BaseModel):
    protocol: ProtocolName
    asset: str
    amount: float
    usd_value: float
    apy: Optional[float]


class HealthScore(BaseModel):
    protocol: ProtocolName
    score: float


class DeFiAccountSnapshot(BaseModel):
    user_address: str
    timestamp: int
    collaterals: List[Collateral]
    borrowings: List[Borrowing]
    staked_positions: List[StakedPosition]
    health_scores: List[HealthScore]
    total_apy: Optional[float]


class PortfolioSnapshot(BaseModel):
    """
    Historical snapshot of a user's DeFi portfolio for timeline visualization.
    Used for time-series storage and retrieval.
    """

    user_address: str
    timestamp: int  # Unix timestamp (UTC)
    total_collateral: float
    total_borrowings: float
    total_collateral_usd: float
    total_borrowings_usd: float
    aggregate_health_score: Optional[float]
    aggregate_apy: Optional[float]
    collaterals: List[Collateral]
    borrowings: List[Borrowing]
    staked_positions: List[StakedPosition]
    health_scores: List[HealthScore]
    protocol_breakdown: dict  # {protocol_name: {...metrics...}}
