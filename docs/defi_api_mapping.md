# DeFi Protocol Data Mapping → Agnostic Pydantic Models

This document describes how to map data from major DeFi protocols (Aave, Compound, Radiant) to the agnostic Pydantic models defined in `backend/app/schemas/defi.py`.

## Integration Approach

> **Note:** With the exception of Radiant, these protocols do not provide a public REST API for user/account data. Data is fetched via:
> - **On-chain contract calls** (used for Radiant)
> - **Subgraph queries** (used for Aave and Compound)

The table below lists the data source for each protocol.

---

| Protocol  | Data Needed         | How to Get It (Contract/Subgraph)                                   | Pydantic Model   | Model Field      |
|-----------|---------------------|---------------------------------------------------------------------|------------------|------------------|
| **Aave**  | Collateral, Debt    | `userReserves` (Aave V2 Subgraph)                                   | Collateral, Borrowing | asset, amount    |
|           | Health Factor       | `user` (Aave V2 Subgraph)                                           | HealthScore      | score            |
|           | APY, Rates          | `reserves` (Aave V2 Subgraph)                                       | StakedPosition   | apy              |
| **Compound** | Collateral, Debt | `account.tokens` (Compound V2 Subgraph)                             | Collateral, Borrowing | asset, amount    |
|           | Health              | `account.health` (Compound V2 Subgraph)                             | HealthScore      | score            |
|           | APY                 | `market.supplyRate`, `market.borrowRate` (Compound V2 Subgraph)     | StakedPosition   | apy              |
| **Radiant** | Collateral, Debt  | `getMTokenData`, `getFDInterestData` (Radiant DataProvider contract)  | Collateral, Borrowing | asset, amount    |
|           | Health Factor       | `getMTokenData` (Radiant DataProvider contract)                     | HealthScore      | score            |
|           | APY                 | `getFDInterestData` (Radiant DataProvider contract)                 | StakedPosition   | apy              |

---

## Example: Aave (V2)
- **Data Source:** [Aave V2 Subgraph](https://thegraph.com/hosted-service/subgraph/aave/protocol-v2)
- **Key Entities:**
  - `userReserves` → Collateral, Borrowing
  - `user.healthFactor` → HealthScore

## Example: Compound (V2)
- **Data Source:** [Compound V2 Subgraph](https://thegraph.com/hosted-service/subgraph/graphprotocol/compound-v2)
- **Key Entities:**
  - `account.tokens` → Collateral, Borrowing
  - `account.health` → HealthScore
  - `market.supplyRate` → APY

## Example: Radiant (V2 - Arbitrum)
- **Data Source:** Direct smart contract calls (see [radiant_arbitrum_contracts.md](./radiant_arbitrum_contracts.md) for details)
- **Key Methods:**
  - `getMTokenData` (from DataProvider contract)
  - `getFDInterestData` (from DataProvider contract)
- **Note:** This method provides live, on-chain data and does not rely on a subgraph.

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