# DeFi Tracker – Documentation & Knowledge Transfer Outline

> Version 0.1 – *draft generated 2025-06-16*

## Table of Contents
1. Overview & Vision
2. Architecture
   2.1 High-Level Diagram
   2.2 Component Breakdown
   2.3 Data Flow & Event Model
3. Backend
   3.1 Tech Stack & Rationale (FastAPI, PostgreSQL/SQLite, Celery, Redis)
   3.2 Domain Models & Services
   3.3 API Contract (OpenAPI)
   3.4 Snapshot Aggregation Service Details
   3.5 Deployment & Ops Considerations
4. Frontend
   4.1 Tech Stack & Rationale (React, Recharts, MUI)
   4.2 State Management & Data Fetching (React Query)
   4.3 TimelineChart Component & Filters
   4.4 Testing Strategy (RTL, Storybook, Cypress)
5. Testing & QA
   5.1 Coverage Goals & CI Gates
   5.2 Test Directory Conventions
   5.3 Mocking External APIs (responses, MSW)
   5.4 Property-Based Testing (Hypothesis)
   5.5 Performance & Security Testing
6. Deployment Pipeline
   6.1 GitHub Actions Overview
   6.2 Docker & Compose Services
   6.3 Environment & Secrets Management
7. Knowledge Transfer & Onboarding
   7.1 Slide Deck Summary
   7.2 Live Walkthrough Checklist
   7.3 FAQ & Troubleshooting
8. Glossary & References

---

## 1. Overview & Vision
SmartWalletFX's **DeFi Tracker** centralises on-chain positions from major lending protocols (Aave, Compound, Radiant…) and offers a historical performance timeline, enabling users to analyse collateral, borrowings and health-score trends.  The tracker serves three strategic purposes:

1. **Portfolio Transparency** – give traders a single source of truth across chains/protocols.
2. **Analytics Foundation** – raw timeline data powers future dashboards (PnL, risk) and alerting.
3. **Extensibility** – modular hexagonal backend and chart-centric frontend facilitate rapid protocol expansion.

The current MVP targets read-only wallet tracking (no Tx signing) with SQLite/PostgreSQL storage, scheduled snapshots and a React chart interface.

## 2. Architecture (summary)
See [System Architecture](defi_architecture.md) for full diagrams.

Key decisions:
- **Hexagonal (ports & adapters)** – isolates domain logic from frameworks (FastAPI, Celery).
- **Async FastAPI** – non-blocking request handling, WebSocket-ready.
- **Celery workers** – decouple heavy RPC calls & allow scalable snapshot jobs.
- **React + Recharts** – SVG charting with minimal bundle size and composability.

_Data flow:_ Browser → Nginx → FastAPI → Redis/PostgreSQL; async workers gather data via Web3.py and cache in DB.

## 3. Backend
Full details in [defi_architecture.md](defi_architecture.md) and [defi_backend_api.md](defi_backend_api.md).
- **Tech Stack**: FastAPI, SQLAlchemy (async), Celery, Redis, PostgreSQL.
- **Domain Models**: `PortfolioSnapshot`, `DeFiAccountSnapshot`, `PortfolioMetrics`.
- **Services**: `SnapshotAggregationService`, `PortfolioSnapshotStore`.
- **OpenAPI** automatically published; TypeScript SDK generated via `openapi-typescript-codegen`.

## 4. Frontend
- **Tech Stack**: React 18, TypeScript, Material UI, Recharts, React Query.
- **Components**: `TimelineChart`, filter controls, `PerformanceTimeline` page.
- **State Management**: React Query caches API responses; SWR pattern.

## 5. Testing & QA
Refer to [Testing & QA Guide](defi_testing_guide.md).
- Coverage gates enforced in CI (90 % backend / 75 % frontend).
- Mocking strategy: `responses` (backend), `msw` (frontend).
- Property-based tests with Hypothesis for numeric edge cases.
- Cypress E2E across desktop & mobile viewports.

## 6. Deployment Pipeline
- GitHub Actions jobs: **security → quality → test → e2e → deploy**.
- Docker images published to GHCR; Docker Compose for local dev.
- Environment variables managed via `.env` and repository secrets.

## 7. Knowledge Transfer & Onboarding
- Slide deck: [defi_knowledge_transfer.md](defi_knowledge_transfer.md)
- Live walkthrough checklist (see deck).  New developers should read architecture & API docs first, then follow local setup in README.

## 8. Glossary & References
- **PortfolioSnapshot** – DB row storing collateral, borrows, health score at timestamp.
- **TimelineResponse** – API wrapper providing snapshots + pagination metadata.
- **Health Score** – risk metric from protocol (Aave, Radiant) indicating liquidation proximity.
- **RPC** – Remote Procedure Call node for blockchain interaction (Alchemy, Infura).

*(Further sections to be populated in subsequent steps.)* 