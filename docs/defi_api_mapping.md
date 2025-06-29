# DeFi Protocol Data Mapping → Agnostic Pydantic Models

This document describes how to map data from major DeFi protocols (Aave, Compound, Radiant) to the agnostic Pydantic models defined in `backend/app/schemas/defi.py`.

## Integration Approach

> **Note:** All protocol data for every supported protocol (Aave, Compound, Radiant) is fetched **directly from on-chain smart contracts** via web3.py. Subgraphs have been fully deprecated.

The table below lists the data source for each protocol.

---

| Protocol               | Data Needed      | Key Contract Calls (Ethereum main-net unless noted)                                               | Pydantic Model        | Model Field   |
| ---------------------- | ---------------- | ------------------------------------------------------------------------------------------------- | --------------------- | ------------- |
| **Aave V3**            | Collateral, Debt | `UiPoolDataProvider` → `getUserReservesData`<br>`AaveProtocolDataProvider` → `getUserReserveData` | Collateral, Borrowing | asset, amount |
|                        | Health Factor    | `UiPoolDataProvider` → `getUserSummaryData`                                                       | HealthScore           | score         |
|                        | APY, Rates       | `UiPoolDataProvider` → `getReservesData`                                                          | StakedPosition        | apy           |
| **Compound V2**        | Collateral, Debt | `CompoundLens` → `getAccountLimits` & `cTokenBalancesAll`<br>`Comptroller` → `getAssetsIn`        | Collateral, Borrowing | asset, amount |
|                        | Health           | `CompoundLens` → `getAccountLimits`                                                               | HealthScore           | score         |
|                        | APY              | Each cToken contract → `supplyRatePerBlock`, `borrowRatePerBlock`                                 | StakedPosition        | apy           |
| **Radiant (Arbitrum)** | Collateral, Debt | `DataProvider` → `getMTokenData`                                                                  | Collateral, Borrowing | asset, amount |
|                        | Health Factor    | `DataProvider` → `getMTokenData`                                                                  | HealthScore           | score         |
|                        | APY              | `DataProvider` → `getFDInterestData`                                                              | StakedPosition        | apy           |

---

## Example: Aave V3 (Main-net)

- **Core contracts used:**
  - `UiPoolDataProvider` `0x3F78BBD206e4D3c504Eb854232EdA7e47E9Fd8FC`
  - `AaveProtocolDataProvider` `0x497a1994c46d4f6C864904A9f1fac6328Cb7C8a6`
- **Typical flow:** call `getUserReservesData(address)` → map to Collateral/Borrowings; call `getUserSummaryData(address)` → map to HealthScore; fetch reserve-level rate data via `getReservesData()` for APY.

## Example: Compound V2 (Main-net)

- **Core contracts used:**
  - `CompoundLens` `0xd513d22422a3062bd342ae374b4b9c20e3a666c1`
  - `Comptroller` `0x3d9819210A31B4961b30EF54bE2aeD79B9c9Cd3B`
- **Typical flow:** `getAccountLimits(address)` returns liquidity & shortfall (health); `cTokenBalancesAll()` returns per-market balances; per-market rate data pulled directly from each cToken.

## Example: Radiant (Arbitrum)

- **Data Source:** Direct calls to Radiant's `DataProvider` contract (see [radiant_arbitrum_contracts.md](./radiant_arbitrum_contracts.md)).
- **Typical flow:** `getMTokenData(address)` → positions & health; `getFDInterestData()` → APY.

---

## Notes

- Fields not present in some protocols are set to `None` or ignored.
- The `DeFiAccountSnapshot` model aggregates all user data at a given timestamp, regardless of protocol.
- This structure makes it easy to add new protocols or fields without major backend refactoring.
- If you want to expose a REST API, you must build your own backend wrapper around these contract calls.

---

## Backend Data Model Usage

The Pydantic models defined in `backend/app/schemas/defi.py` serve as the canonical schema for DeFi user data aggregation and storage. They are used to:

- Normalize and validate data ingested from protocol-specific sources (on-chain contracts).
- Provide a unified interface for backend logic, API endpoints, and local persistence.
- Serve as a reference for designing SQLAlchemy models if/when persistent storage of DeFi snapshots is required.

**Best practices:**

- Always map protocol-specific data to these models before persisting or exposing via API.
- Extend these models as needed to support new protocols or additional data fields.
- Use these models as the single source of truth for DeFi data structure in the backend.

For more details, see the docstring in `backend/app/schemas/defi.py`.
