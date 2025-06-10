# DeFi Protocol Data Mapping → Agnostic Pydantic Models

This document describes how to map data from major DeFi protocols (Aave, Compound, Radiant) to the agnostic Pydantic models defined in `backend/app/schemas/defi.py`.

## Integration Approach

> **Note:** None of these protocols provide a public REST API for user/account data. All data must be fetched via:
> - **On-chain contract calls** (using protocol-specific smart contracts)
> - **Subgraph queries** (if available, via The Graph)

The table below lists the recommended contract methods and subgraph entities for each protocol and data type.

---

| Protocol  | Data Needed         | How to Get It (Contract/Subgraph)                                   | Pydantic Model   | Model Field      |
|-----------|---------------------|---------------------------------------------------------------------|------------------|------------------|
| **Aave**  | Collateral, Debt    | `getUserReservesData(address user)` (ProtocolDataProvider contract) <br> or `userReserves` (Aave Subgraph) | Collateral, Borrowing | asset, amount    |
|           | Health Factor       | `getUserAccountData(address user)` (ProtocolDataProvider contract) <br> or `userAccountData` (Aave Subgraph) | HealthScore      | score            |
|           | APY, Rates          | `getReserveData(address asset)` (contract) <br> or `reserves` (Subgraph) | StakedPosition   | apy              |
| **Compound** | Collateral, Debt | `cToken.balanceOfUnderlying(address)` (cToken contract) <br> `cToken.borrowBalanceCurrent(address)` (cToken contract) <br> or `account.tokens` (Compound Subgraph) | Collateral, Borrowing | asset, amount    |
|           | Health              | `account.health` (Compound Subgraph)                                | HealthScore      | score            |
|           | APY                 | `cToken.supplyRatePerBlock`, `cToken.borrowRatePerBlock` (contract) | StakedPosition   | apy              |
| **Radiant** | Collateral, Debt  | LendingPool/DataProvider contract methods <br> or subgraph (if available) | Collateral, Borrowing | asset, amount    |
|           | Health Factor       | DataProvider contract or subgraph                                   | HealthScore      | score            |
|           | APY                 | DataProvider contract or subgraph                                   | StakedPosition   | apy              |

---

## Example: Aave (V2/V3)
- **Contract:** ProtocolDataProvider (see [Aave docs](https://docs.aave.com/developers/core-contracts/pool-data-provider))
- **Subgraph:** [Aave Subgraph](https://thegraph.com/hosted-service/subgraph/aave/protocol-v2)
- **Methods:**
  - `getUserReservesData(address user)` → Collateral, Borrowing
  - `getUserAccountData(address user)` → HealthScore

## Example: Compound
- **Contract:** cToken contracts (see [Compound docs](https://docs.compound.finance/v2/ctokens/))
- **Subgraph:** [Compound Subgraph](https://thegraph.com/hosted-service/subgraph/graphprotocol/compound-v2)
- **Methods:**
  - `balanceOfUnderlying(address)` (cToken) → Collateral
  - `borrowBalanceCurrent(address)` (cToken) → Borrowing
  - `supplyRatePerBlock`, `borrowRatePerBlock` (cToken) → APY

## Example: Radiant
- **Contract:** LendingPool/DataProvider (see [Radiant docs](https://docs.radiant.capital/))
- **Subgraph:** If available, use the Radiant subgraph for user/account data.

---

## Notes
- Fields not present in some protocols are set to `None` or ignored.
- The `DeFiAccountSnapshot` model aggregates all user data at a given timestamp, regardless of protocol.
- This structure makes it easy to add new protocols or fields without major backend refactoring. 
- If you want to expose a REST API, you must build your own backend wrapper around these contract/subgraph calls.

---

## Backend Data Model Usage

The Pydantic models defined in `backend/app/schemas/defi.py` serve as the canonical schema for DeFi user data aggregation and storage. They are used to:
- Normalize and validate data ingested from protocol-specific sources (on-chain contracts, subgraphs).
- Provide a unified interface for backend logic, API endpoints, and local persistence.
- Serve as a reference for designing SQLAlchemy models if/when persistent storage of DeFi snapshots is required.

**Best practices:**
- Always map protocol-specific data to these models before persisting or exposing via API.
- Extend these models as needed to support new protocols or additional data fields.
- Use these models as the single source of truth for DeFi data structure in the backend.

For more details, see the docstring in `backend/app/schemas/defi.py`. 