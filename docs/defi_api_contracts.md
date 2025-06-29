# DeFi Tracker – API Contracts (Summary)

> See `docs/defi_backend_api.md` for full field-level documentation and examples.

## 1. Public REST Endpoints

| Method | Path                        | Description                                            | Auth | Notes                                                                          |
| ------ | --------------------------- | ------------------------------------------------------ | ---- | ------------------------------------------------------------------------------ |
| GET    | `/defi/portfolio/{address}` | Live aggregate of collateral, borrowings, health score | None | Wraps on-chain data from supported protocols                                   |
| GET    | `/defi/timeline/{address}`  | Historical snapshots timeline                          | None | Supports `from_ts`, `to_ts`, `limit`, `offset`, `interval`, `raw` query params |
| GET    | `/defi/radiant/{address}`   | Radiant single-protocol snapshot                       | None | Arbitrum network                                                               |
| GET    | `/defi/aave/{address}`      | Aave single-protocol snapshot                          | None | Mainnet                                                                        |
| GET    | `/defi/compound/{address}`  | Compound single-protocol snapshot                      | None | Mainnet                                                                        |

### Response Models

- **PortfolioMetrics** – returned by `/defi/portfolio` (see backend doc).
- **TimelineResponse** – default wrapper for `/defi/timeline`; optionally plain `PortfolioSnapshot[]` when `raw=true`.
- **DeFiAccountSnapshot** – base model for each protocol-specific endpoint.

## 2. Admin / Internal Endpoints

| Method | Path                           | Description                                                | Auth        | Notes                  |
| ------ | ------------------------------ | ---------------------------------------------------------- | ----------- | ---------------------- |
| POST   | `/defi/admin/trigger-snapshot` | Manually trigger snapshot aggregation for selected wallets | JWT (admin) | Returns Celery task ID |

## 3. OpenAPI & Client Generation

- The FastAPI application exposes OpenAPI JSON at `/openapi.json` and Swagger UI at `/docs`.
- CI job `generate-typescript-sdk` runs `openapi-typescript-codegen` to publish an NPM package (`@defi-tracker/sdk`).

## 4. Versioning Strategy

- API follows **semantic versioning** via URL prefix (currently `/`).
- Breaking changes will bump the major version; new fields are considered non-breaking.

## 5. Future Additions

- WebSocket channel `ws://{host}/defi/portfolio/stream/{address}` (Phase 3).
- Batch timeline endpoint to fetch multiple addresses in one call.
