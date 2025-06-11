# DeFi Backend API Documentation

## Overview
This backend provides a unified API for fetching DeFi account data across multiple protocols (Radiant, Aave, Compound). It aggregates user positions (collateral, borrowings, health score, etc.) into a common data model, making it easy to build dashboards, analytics, or portfolio tools.

## Supported Protocols
- **Radiant** (Arbitrum)
  - Data Source: Direct smart contract calls using web3.py (no longer uses subgraph)
  - See [radiant_arbitrum_contracts.md](./radiant_arbitrum_contracts.md) for contract addresses, ABI, and config instructions.
- **Aave** (Ethereum Mainnet)
  - Subgraph: https://thegraph.com/hosted-service/subgraph/aave/protocol-v2
- **Compound** (Ethereum Mainnet)
  - Subgraph: https://thegraph.com/hosted-service/subgraph/graphprotocol/compound-v2

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

### Portfolio Aggregation (NEW)
```
GET /defi/portfolio/{address}
```
- **Success:** 200 OK, returns PortfolioMetrics (aggregated across all supported protocols)
- **Not Found:** 200 OK with zeroed fields if user not found on any protocol

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
- `total_collateral_usd`: USD value of all collateral (dummy, 1:1 for now)
- `total_borrowings_usd`: USD value of all borrowings (dummy, 1:1 for now)
- `aggregate_health_score`: Average health score across protocols
- `aggregate_apy`: Weighted average APY across all staked positions
- `collaterals`, `borrowings`, `staked_positions`, `health_scores`: Flattened lists from all protocols
- `protocol_breakdown`: Per-protocol metrics and positions (see ProtocolBreakdown model)
- `historical_snapshots`: (optional, null for now) Placeholder for future historical data
- `timestamp`: ISO8601 UTC timestamp of aggregation

#### ProtocolBreakdown Model
- `protocol`: Protocol name (e.g., "aave")
- `total_collateral`, `total_borrowings`: Sums for this protocol
- `aggregate_health_score`, `aggregate_apy`: Protocol-specific metrics
- `collaterals`, `borrowings`, `staked_positions`, `health_scores`: Lists for this protocol

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

## Alembic Database Migration Setup (Step-by-Step Guide)

To manage database schema changes, this project uses Alembic. Here's how to set it up and use it for new features (e.g., the PortfolioSnapshot timeline):

1. **Install Alembic**
   - Already included in `requirements/base.txt`.

2. **Initialize Alembic**
   - From the `backend/` directory, run:
     ```bash
     alembic init migrations
     ```
   - This creates a `migrations/` directory and `alembic.ini` config file.

3. **Configure Database URL**
   - Edit `backend/alembic.ini` and set the `sqlalchemy.url` to your database (e.g., SQLite, PostgreSQL).

4. **Import Models in env.py**
   - Edit `backend/migrations/env.py` to import your SQLAlchemy `Base` and all models (including `PortfolioSnapshot`).
   - Example:
     ```python
     from app.models.portfolio_snapshot import PortfolioSnapshot
     from app.models import Base
     target_metadata = Base.metadata
     ```

5. **Generate a Migration**
   - After adding or changing models, run:
     ```bash
     alembic revision --autogenerate -m "create portfolio_snapshots table"
     ```

6. **Apply the Migration**
   - Run:
     ```bash
     alembic upgrade head
     ```

7. **Repeat for Future Changes**
   - For new models or schema changes, repeat steps 5-6.

**Example:**
- The PortfolioSnapshot model for the timeline feature is managed via Alembic migrations. 