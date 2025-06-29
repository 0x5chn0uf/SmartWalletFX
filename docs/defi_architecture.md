# DeFi Tracker – System Architecture

> Version 0.1 – drafted 2025-06-16

## 1. High-Level Overview

```
mermaid
flowchart LR
    Browser -->|HTTPS| Nginx
    Nginx -->|REST| FastAPI
    FastAPI -->|SQLAlchemy (async)| PostgreSQL[(PostgreSQL / SQLite)]
    FastAPI --> CeleryBroker((Redis Broker))
    CeleryWorker((Celery Worker)) -->|SQLAlchemy| PostgreSQL
    CeleryWorker -->|Web3.py| EthereumRPC[(Alchemy / Infura)]
    CeleryWorker -->|HTTP| DeBankAPI[(DeBank / CoinGecko)]
```

- **Browser / SPA**: React single-page application served by Nginx (built artefacts).
- **API Gateway**: Nginx proxies `/api/*` to FastAPI, serves static assets for everything else.
- **FastAPI**: Handles synchronous HTTP requests, aggregates live data, exposes OpenAPI.
- **Celery Workers**: Perform periodic snapshot aggregation and heavy tasks asynchronously.
- **Redis**: Acts as both Celery broker and short-lived cache for token prices.
- **PostgreSQL / SQLite**: Stores historical snapshots and user metadata (SQLite in dev/test, PostgreSQL in staging/prod).
- **Web3.py**: Reads on-chain data from supported protocols via RPC nodes.

## 2. Layered Hexagonal Design

| Layer              | Responsibility                                    | Key Modules                                |
| ------------------ | ------------------------------------------------- | ------------------------------------------ |
| **Domain**         | Entities, value objects, business rules           | `app/domain/` – `portfolio.py`, `token.py` |
| **Application**    | Use cases, services, orchestration                | `app/services/`, `app/use_cases/`          |
| **Adapters**       | DB repositories, protocol adapters, external APIs | `app/adapters/`, `app/repositories/`       |
| **Infrastructure** | Framework glue (FastAPI, Celery, DI, config)      | `app/api/`, `app/core/`, `app/tasks/`      |

Dependencies point **inward** only (outer → inner). Application & Domain layers are independent of FastAPI/Celery.

## 3. Key Components

### 3.1 SnapshotAggregationService

Location: `app/services/snapshot_aggregation.py`

- Collects live balances from supported protocols for a wallet.
- Persists `PortfolioSnapshot` ORM rows via injected `AsyncSession`.
- Exposed as DI dependency to Celery & FastAPI admin endpoints.

### 3.2 PortfolioSnapshotStore

- Repository offering query helpers and timeline aggregation.
- Used by `/defi/timeline` endpoint and SnapshotAggregationService.

### 3.3 Celery Task Flow

```
periodic beat → snapshot_all_wallets → SnapshotAggregationService.collect_snapshot → DB
```

### 3.4 React Frontend

- **TimelineChart** (Recharts) displays historical data from `/defi/timeline`.
- **React Query** drives fetching / caching.
- **MUI** provides responsive UI components.

## 4. Deployment

- **Docker Compose** for local dev (`docker-compose.yml`).
- **GitHub Actions** builds backend & frontend images, pushes to GHCR.
- **CI Jobs**: lint, tests, coverage gates, Cypress E2E (parallel).
- **Prod**: Kubernetes helm chart (planned) or AWS ECS Fargate (MVP).

## 5. Security Considerations

- JWT auth for protected admin endpoints (future Task 4).
- Secrets mounted via Docker/CI secrets; never committed.
- API rate-limiting via Nginx & token bucket.

## 6. Future Work

- Switch to **Event-Driven** architecture using Kafka for real-time updates.
- Introduce GraphQL gateway for aggregated queries.
