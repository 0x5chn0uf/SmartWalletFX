# DeFi Backend API Documentation

## Overview
This backend provides a unified API for fetching DeFi account data across multiple protocols (Radiant, Aave, Compound). It aggregates user positions (collateral, borrowings, health score, etc.) into a common data model, making it easy to build dashboards, analytics, or portfolio tools.

## Supported Protocols
- **Radiant** (Arbitrum)
  - Data Source: Direct smart contract calls using web3.py.
  - See [radiant_arbitrum_contracts.md](./radiant_arbitrum_contracts.md) for contract addresses, ABI, and config instructions.
- **Aave** (Ethereum Mainnet)
  - Data Source: TheGraph Subgraph (`https://thegraph.com/hosted-service/subgraph/aave/protocol-v2`)
- **Compound** (Ethereum Mainnet)
  - Data Source: TheGraph Subgraph (`https://thegraph.com/hosted-service/subgraph/graphprotocol/compound-v2`)

## API Endpoints
All endpoints return a `DeFiAccountSnapshot` for a given wallet address.

### Radiant
```
GET /defi/radiant/{address}
```
- **Success:** 200 OK, returns DeFiAccountSnapshot
- **Not Found:** 404 if user not found on-chain
- **Note:** Data is fetched live from Radiant contracts on Arbitrum using web3.py. Requires `ARBITRUM_RPC_URL` to be set in config. See [radiant_arbitrum_contracts.md](./radiant_arbitrum_contracts.md) for details on updating contract addresses, ABI files, and config.

### Aave
```
GET /defi/aave/{address}
```
- **Success:** 200 OK, returns DeFiAccountSnapshot
- **Not Found:** 404 if user not found on subgraph

### Compound
```
GET /defi/compound/{address}
```
- **Success:** 200 OK, returns DeFiAccountSnapshot
- **Not Found:** 404 if user not found on subgraph

### Portfolio Aggregation (Live)
```
GET /defi/portfolio/{address}
```
- Fetches live data from all supported protocols and returns an on-the-fly aggregated `PortfolioMetrics` view.
- **Success:** 200 OK, returns PortfolioMetrics
- **Not Found:** 200 OK with zeroed fields if user not found on any protocol

### Performance Timeline (Historical)
```
GET /defi/timeline/{address}
```

Returns the historical portfolio **timeline** for a wallet address. Data comes from `PortfolioSnapshot` rows collected by the Celery background task.

#### Query Parameters

| Name       | Type   | Default | Description |
|------------|--------|---------|-------------|
| `from_ts`  | int    | **required** | Unix timestamp (inclusive) marking the **start** of the range |
| `to_ts`    | int    | **required** | Unix timestamp (inclusive) marking the **end** of the range |
| `limit`    | int    | `100`   | Max number of snapshots to return (capped at `1000`) |
| `offset`   | int    | `0`     | Number of snapshots to skip (basic pagination) |
| `interval` | enum   | `none`  | Aggregation interval (`none`, `daily`, `weekly`) |
| `raw`      | bool   | `false` | If **true**, returns a plain `PortfolioSnapshot[]` list for backwards compatibility. |

#### Default Response (`raw=false`)

The default response is wrapped in a `TimelineResponse` object that includes useful metadata for pagination and charting:

```jsonc
{
  "snapshots": [
    {
      "user_address": "0x123...",
      "timestamp": 1718294400,
      "total_collateral": 1500,
      "total_borrowings": 200.5,
      "total_collateral_usd": 1500,
      "total_borrowings_usd": 200.5,
      "aggregate_health_score": 1.95,
      "aggregate_apy": 0.04,
      "collaterals": [],
      "borrowings": [],
      "staked_positions": [],
      "health_scores": [],
      "protocol_breakdown": {}
    }
  ],
  "interval": "none",
  "limit": 100,
  "offset": 0,
  "total": 1
}
```

#### Raw Response (`raw=true`)

Setting `raw=true` returns the legacy plain list with no metadata:

```jsonc
[
  { "user_address": "0x123...", "timestamp": 1718294400, "total_collateral": 1500, ... }
]
```

This flag exists to avoid breaking older consumers while new clients migrate to the richer `TimelineResponse` wrapper.

### Admin: Trigger Snapshot
```
POST /defi/admin/trigger-snapshot
```
- Manually triggers the Celery background task to collect and store a portfolio snapshot for all tracked wallets.
- This is an admin-only endpoint and requires appropriate authentication.
- **Success:** 202 Accepted, returns the Celery task ID.
- **Body:**
  ```json
  {
    "wallet_addresses": ["0x...", "0x..."]
  }
  ```

#### Example Response
```json
{
  "user_address": "0x123...",
  "total_collateral": 1500,
  "total_borrowings": 200.5,
  "total_collateral_usd": 1500,
  "total_borrowings_usd": 200.5,
  "aggregate_health_score": 1.95,
  "aggregate_apy": 0.04,
  "collaterals": [
    {"protocol": "AAVE", "asset": "DAI", "amount": 1000, "usd_value": 0},
    {"protocol": "COMPOUND", "asset": "USDC", "amount": 500, "usd_value": 0}
  ],
  "borrowings": [
    {"protocol": "AAVE", "asset": "DAI", "amount": 200, "usd_value": 0, "interest_rate": 0.07},
    {"protocol": "COMPOUND", "asset": "ETH", "amount": 0.5, "usd_value": 0, "interest_rate": null}
  ],
  "staked_positions": [
    {"protocol": "AAVE", "asset": "DAI", "amount": 1000, "usd_value": 0, "apy": 0.04}
  ],
  "health_scores": [
    {"protocol": "AAVE", "score": 2.1},
    {"protocol": "COMPOUND", "score": 1.8}
  ],
  "protocol_breakdown": {
    "aave": {
      "protocol": "aave",
      "total_collateral": 1000,
      "total_borrowings": 200,
      "aggregate_health_score": 2.1,
      "aggregate_apy": 0.04,
      "collaterals": [ ... ],
      "borrowings": [ ... ],
      "staked_positions": [ ... ],
      "health_scores": [ ... ]
    },
    "compound": {
      "protocol": "compound",
      "total_collateral": 500,
      "total_borrowings": 0.5,
      "aggregate_health_score": 1.8,
      "aggregate_apy": null,
      "collaterals": [ ... ],
      "borrowings": [ ... ],
      "staked_positions": [ ... ],
      "health_scores": [ ... ]
    },
    "radiant": {
      "protocol": "radiant",
      "total_collateral": 0,
      "total_borrowings": 0,
      "aggregate_health_score": null,
      "aggregate_apy": null,
      "collaterals": [],
      "borrowings": [],
      "staked_positions": [],
      "health_scores": []
    }
  },
  "historical_snapshots": null,
  "timestamp": "2024-06-13T12:34:56.789Z"
}
```

#### Model Fields (PortfolioMetrics)
- `user_address`: Wallet address
- `total_collateral`: Sum of all collateral amounts across protocols
- `total_borrowings`: Sum of all borrowings across protocols
- `total_collateral_usd`: USD value of all collateral
- `total_borrowings_usd`: USD value of all borrowings
- `aggregate_health_score`: Average health score across protocols
- `aggregate_apy`: Weighted average APY across all staked positions
- `collaterals`, `borrowings`, `staked_positions`, `health_scores`: Flattened lists from all protocols
- `protocol_breakdown`: Per-protocol metrics and positions (see ProtocolBreakdown model)
- `historical_snapshots`: **(DEPRECATED)** This field is no longer used in the live aggregation response. Use the `/defi/timeline/{address}` endpoint instead.
- `timestamp`: ISO8601 UTC timestamp of aggregation

#### ProtocolBreakdown Model
- `protocol`: Protocol name (e.g., "aave")
- `total_collateral`, `total_borrowings`: Sums for this protocol
- `aggregate_health_score`, `aggregate_apy`: Protocol-specific metrics
- `collaterals`, `borrowings`, `staked_positions`, `health_scores`: Lists for this protocol
- `DeFiAccountSnapshot`: Aggregates all above for a user at a timestamp.
- `PortfolioMetrics`: Aggregated portfolio view (see above for fields).
- `ProtocolBreakdown`: Per-protocol breakdown (see above).
- `PortfolioSnapshot`: A full portfolio snapshot stored in the database, including all metrics and breakdowns for a specific point in time.

## Data Model
See `backend/app/schemas/defi.py` for full details. Key models:
- `Collateral`: protocol, asset, amount, usd_value
- `Borrowing`: protocol, asset, amount, usd_value, interest_rate
- `StakedPosition`: protocol, asset, amount, usd_value, apy
- `HealthScore`: protocol, score
- `DeFiAccountSnapshot`: Aggregates all above for a user at a timestamp
- `PortfolioMetrics`: Aggregated portfolio view (see above for fields)
- `ProtocolBreakdown`: Per-protocol breakdown (see above)

## Extending
To add a new protocol:
1. Create a new usecase in `backend/app/usecase/` to fetch and map data.
2. Add an endpoint in `backend/app/api/endpoints/defi.py`.
3. Add unit/integration tests.
4. Update this documentation.

## Testing & Linting
- Run all tests:
  ```
  cd backend
  PYTHONPATH=$(pwd) pytest --cov=app --cov-report=term-missing
  ```
- Run linters:
  ```
  black . && isort . && flake8 .
  ```

## Known Limitations
- `usd_value` is always 0 (no price oracle integration yet)
- `timestamp` is always 0 (not set to block or system time)
- No rate limiting or advanced error handling
- No pagination/filtering on endpoints
- Only supports Radiant (Arbitrum), Aave, and Compound (Ethereum Mainnet)
- `usd_value`, `total_collateral_usd`, `total_borrowings_usd` are dummy (no price oracle yet)
- `timestamp` is set to system UTC time, not block time

## Quickstart for Developers
1. Clone the repo and set up the Python environment
2. Install dependencies in `backend/`
3. Run the FastAPI server and visit `/docs` for OpenAPI
4. Use the endpoints above to fetch DeFi data 

## Database Migrations (Alembic)
This project uses Alembic to manage database schema changes.

- **To generate a new migration after changing a model:**
  ```bash
  # From the backend/ directory
  alembic revision --autogenerate -m "Your descriptive message"
  ```
- **To apply migrations to the database:**
  ```bash
  alembic upgrade head
  ```

All schema changes, such as adding the `PortfolioSnapshot` table, must be handled through Alembic migrations. 

## Dynamic Protocol Adapters & Aggregation (2025-02-18)

The `/defi/timeline` endpoint (and portfolio metrics endpoints) no longer rely on a hard-coded list of on-chain protocols.  A new pluggable architecture allows adding or removing protocols by simply registering a subclass of `ProtocolAdapter`:

```python
from app.adapters.protocols.base import ProtocolAdapter

class MyProtocolAdapter(ProtocolAdapter):
    name = "myprotocol"

    async def fetch_snapshot(self, address: str):
        # return DeFiAccountSnapshot | None
```

All registered adapters are injected into the **dynamic aggregator** (`aggregate_portfolio_metrics_from_adapters`) which merges snapshots into a single `PortfolioMetrics` object consumed by `SnapshotAggregationService`.

Key points:
1. **Adapters live in** `app.adapters.protocols.*`  
   Current adapters: `AaveContractAdapter`, `CompoundContractAdapter`, `RadiantContractAdapter`.
2. **Dependency Injection** – `app.di.get_snapshot_service_sync` & FastAPI dependency override build the adapter list and aggregator at runtime.
3. **Testing** – `tests/integration/test_timeline_dynamic_aggregator.py` overrides the FastAPI dependency to inject a dummy aggregator, proving `/defi/timeline/{address}` works end-to-end with the new architecture.

No API contract changes: existing consumers can continue to hit `/defi/timeline` with the same query parameters.  New protocols appear automatically in the `protocol_breakdown` field of responses once their adapters are implemented. 