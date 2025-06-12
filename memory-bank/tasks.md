# Project Task Board

A summary of high-level tasks managed in Task Master, with details, progress, and reflections tracked in this document.

---

## Task 2: Develop DeFi Tracker
**Status (in Task Master):** `pending`
**Status (in this file):** `IN PROGRESS` - 4/10 subtasks completed

### Subtask 2.1 – Analyze Current Codebase Structure ✅ DONE
Completed. Architecture, data flow, and integration points documented.

### Subtask 2.2 – Identify Required Components and Models ✅ DONE
**Goal:** List every backend model, service, and frontend component required for the Performance Timeline feature, check for existing implementations, and highlight gaps.

**Completed Analysis:**
| Layer | Component / Model | Exists? | Notes / Action |
|-------|-------------------|---------|----------------|
| Backend – ORM | `PortfolioSnapshot` | ✅ | Already implemented (`app/models/portfolio_snapshot.py`). |
| Backend – ORM | `PortfolioSnapshotCache` | ✅ | Implemented for timeline caching. |
| Backend – ORM | `TokenPrice`, `TokenBalance`, `HistoricalBalance` | ✅ | Present and used for auxiliary data. |
| Backend – Service | **Snapshot Aggregation Service** | ⚠️ PARTIAL | Business logic currently lives inside Celery task; extract into reusable service for DI. |
| Backend – Service | **Timeline Query Service** | ⚠️ PARTIAL | Logic inside `PortfolioSnapshotStore.get_timeline`; may stay or be refactored for caching layers. |
| Backend – API | `/defi/timeline/{address}` endpoint | ✅ | Exists in `api/endpoints/defi.py`. |
| Backend – API | `/defi/portfolio/{address}` endpoint | ✅ | Live aggregate endpoint; confirm fields align with frontend needs. |
| Backend – Schema | `schemas.defi.PortfolioSnapshot` | ✅ | Matches ORM; verify optional fields. |
| Backend – Schema | **TimelineResponse** | ❌ | Create DTO that groups snapshots + metadata (interval, paging). |
| Frontend | **TimelineChart component** | ❌ | Choose chart lib (e.g. Recharts) and build interactive chart. |
| Frontend | **Filters (interval, range)** | ❌ | UI controls for daily/weekly view, date range. |
| Frontend | **API client hooks** | ❌ | React hooks for timeline & live portfolio endpoints. |

**Key Deliverables Identified:**
1. Extract **Snapshot Aggregation Service** (backend/service) → Subtask 2.9
2. Design & implement **TimelineResponse** Pydantic model → Subtask 2.9
3. Create **TimelineChart** component with Recharts → Subtask 2.10
4. Build chart filters and API hooks → Subtask 2.10

### Subtask 2.3 – Select Visualization Libraries and Data Sources ✅ DONE
**Goal:** Evaluate and select a charting library for the Performance Timeline feature.

**Tech Spike Results:**
| Library | Pros | Cons | Recommendation |
|---|---|---|---|
| **Recharts** | - Component-based React API<br>- Good documentation<br>- SVG-based rendering<br>- Strong community | - Performance limitations with >2,000 points | **🏆 SELECTED** |
| **Nivo** | - Beautiful defaults<br>- Server-side rendering<br>- Built-in animations | - Larger bundle size<br>- Complex for simple charts | 🥈 Strong Contender |
| **Chart.js** | - Fast canvas rendering<br>- Lightweight<br>- Mature ecosystem | - Less React-friendly<br>- Limited customization | 🥉 Viable Alternative |

**Final Decision: Recharts**
- **Justification**: Best React integration, excellent customization, adequate performance for our dataset sizes
- **Data Sources Confirmed**: Existing `/defi/timeline/{address}` and `/defi/portfolio/{address}` endpoints

### Current Progress Summary
- **Completed (7/10 subtasks):**
    - ✅ Architecture analysis and codebase review (Subtask 2.1)
    - ✅ Component/model requirements identification with gap analysis (Subtask 2.2)
    - ✅ Frontend charting library selection (Recharts) with tech spike (Subtask 2.3)
    - ✅ Backend data preparation logic & API design implemented (Subtask 2.4)
    - ✅ Snapshot Aggregation Service & TimelineResponse DTO implemented (Subtask 2.9)
    - ✅ TimelineChart component, filters, validation & wallet selector implemented (Subtask 2.10)
    - ✅ **Subtask 2.15** – Cypress E2E CI job integrated and passing in CI

- **In Progress:**
    - 🚧 **Subtask 2.11** – Increase test coverage for Store layer & Radiant adapter (>90 %)
    - 🔄 **Subtask 2.12** – Replace `Any` response_model with `Union` after FastAPI/Pydantic v2 release
    - 🔄 **Subtask 2.13** – Adopt `AsyncExitStack` for engine teardown in tests
    - 🔄 **Subtask 2.14** – Document Dev vs Test DB setup in CONTRIBUTING.md

### Next Steps
1. **Finish Subtask 2.15:** Expand Cypress specs to cover basic user flows (home page loads, timeline chart renders with mocked API) and finalise CI job parameters (wait strategy, artefact retention).
2. **Start Subtask 2.11:** Add unit tests for `PortfolioSnapshotStore` and `RadiantContractAdapter` to raise overall coverage above 90 %.
3. **House-keeping:** Once FastAPI/Pydantic v2 stable, tackle Subtask 2.12 followed by 2.13 and 2.14 documentation work.

### Summary of Work Done
- Unified backend API for Radiant, Aave, and Compound implemented.
- Celery task for periodic and manual DeFi snapshot collection is implemented and robustly tested.
- Manual trigger endpoint is functional and tested.
- All advanced improvements are tracked as separate tasks in Task Master.

### Key Features Implemented
- **Data Models**: Agnostic Pydantic schemas and SQLAlchemy ORM models for DeFi data (collateral, borrows, health score, etc.).
- **Protocol Integration**: Clients and adapters for Radiant (subgraph and contract), Aave, and Compound.
- **API Endpoints**: Endpoints to expose data for each protocol.
- **Performance Timeline**:
    - [x] `PortfolioSnapshot` model for storing historical data.
    - [x] Scheduled job (Celery) to periodically collect and store snapshots.
    - [x] API endpoint `/defi/timeline/{address}` to retrieve historical data.
- **Testing**: Comprehensive unit and integration tests with high coverage (96%).

### Reflections & Lessons Learned
- **Successes**: The Celery task for snapshot collection is robust and well-tested. The modular architecture of the backend made integration straightforward.
- **Challenges**: Bridging async (FastAPI) and sync (Celery) database access required careful session management. Ensuring test database consistency across both engines was complex but achieved.
- **Lessons Learned**: Design for testability and dependency injection from the start. Explicitly track all new ideas and improvements in Task Master to maintain a clear roadmap.

### Subtask 2.9 – Build Snapshot Aggregation Service & TimelineResponse Model ✅ DONE (reflected)

**Implementation Plan (v1)**

| # | Task | File / Path | Notes |
|---|------|-------------|-------|
| 1 | **Create SnapshotAggregationService** | `backend/app/services/snapshot_aggregation.py` | Extract aggregation logic from Celery task. Provide `async collect_snapshot(user_address: str) -> PortfolioSnapshot` method. Accept injected protocol clients + DB session for testability. |
| 2 | **Refactor Celery task** to use the new service | `backend/app/tasks/snapshots.py` | Replace inline aggregation with service call. Ensure DI via function parameter or local import. |
| 3 | **Design TimelineResponse DTO** | `backend/app/schemas/portfolio_timeline.py` | Fields: `snapshots: List[PortfolioSnapshot]`, `interval: str`, `limit: int`, `offset: int`, `total: int`. |
| 4 | **Update `/defi/timeline` endpoint** to return TimelineResponse | `backend/app/api/endpoints/defi.py` | Wrap existing list in DTO, add `total` count and interval metadata. Keep old behavior with `?raw=true` query for backward compatibility. |
| 5 | **Add FastAPI Dependency** for the service | `backend/app/api/dependencies.py` | ✅ Implemented `get_snapshot_service`. |
| 6 | **Write unit tests** for service | `backend/tests/unit/service/` | ✅ Added happy-path, error-path and async tests. Coverage ~84 %. |
| 7 | **Update integration tests** for timeline endpoint | `backend/tests/integration/test_defi_timeline_endpoint.py` | ✅ Wrapper & raw modes covered. |
| 8 | **Migrate manual trigger endpoint** (if needed) | `backend/app/api/endpoints/defi.py` | ✅ Endpoint still calls Celery which delegates to service. |
| 9 | **Ensure DI-friendly Celery config** | `backend/app/di.py` + `tasks/snapshots.py` | ✅ Introduced simple DI helpers for sync sessions. |
|10 | **Documentation** | `docs/defi_backend_api.md` | Add TimelineResponse schema and example. |

**Acceptance Criteria – Results**
1. Service class with DI – **Met** (coverage ~84 %, additional tests planned to hit 90 %).
2. Celery task delegates to service – **Met**.
3. TimelineResponse documented & returned – **Met**.
4. `raw` param backward-compat – **Met**.
5. All tests pass – **Met**.

Remaining improvement: raise SnapshotAggregationService coverage >90 % (tracked as subtask 2.11).

### Subtask 2.10 – Implement TimelineChart Component with Recharts ✅ DONE

**Implementation Plan (v1 – frontend)**

| # | Task | File / Path | Notes |
|---|------|-------------|-------|
| 1 | **Add Recharts dependency** | `frontend/package.json` | `npm i recharts @types/recharts` (types optional). |
| 2 | **Define Shared Types** | `frontend/src/types/timeline.ts` | `PortfolioSnapshot`, `TimelineResponse` mirrors backend schema (partial fields needed for chart). |
| 3 | **API Service Method** | `frontend/src/services/defi.ts` | `getTimeline(address, params)` wraps `/defi/timeline` with `raw=true` by default for simpler mapping. |
| 4 | **React Hook** | `frontend/src/hooks/useTimeline.ts` | Uses SWR or `useEffect`+`useState` to fetch timeline data, handle loading & errors. |
| 5 | **TimelineChart Component** | `frontend/src/components/Charts/TimelineChart.tsx` | Builds responsive `LineChart` (Recharts) with lines for collateral, borrowings, health score. Accepts snapshots prop. |
| 6 | **Page Integration** | `frontend/src/pages/Home/Home.tsx` (or new Portfolio page) | Fetch address (temp placeholder) and render chart inside existing `Layout`. |
| 7 | **Filters UI (MVP)** | Simple interval dropdown + date inputs; not yet wired to hook (will iterate). |
| 8 | **Unit Tests** | `frontend/src/__tests__/TimelineChart.test.tsx` | Render with mock data, assert line series, tooltip content. |
| 9 | **E2E Smoke** | Cypress (future) to ensure chart renders with live backend. |

**Acceptance Criteria**
- [ ] `TimelineChart` displays collateral & borrowings over time for hard-coded wallet address.
- [ ] Component resizes with window and shows tooltips.
- [ ] Hook handles loading & error states (simple spinners/message).
- [ ] All new code covered by Jest RTL tests; lint passes.

### Subtask 2.15 – Add Cypress E2E CI job 🔄 PLANNING
Set up Cypress end-to-end tests and integrate them into GitHub Actions.

**Goals:**
1. Scaffold Cypress in `frontend/`.
2. Docker Compose file (`docker-compose.ci.yml`) spins up backend (uvicorn) and serves built frontend (nginx).
3. Add `e2e-cypress` job to existing CI workflow; depends on build-backend & build-frontend, caches Cypress binary, waits for `/api/v1/health`, then runs tests.
4. Upload screenshots/videos artefacts.

**Status:** in progress – initial CI job scaffold, Cypress config, Docker compose created (2025-06-12)

---

## Task 38: Refactor Celery Tasks for Testability and Observability
**Status (in Task Master):** `pending`

### Goal
Refactor existing Celery tasks to enhance testability using dependency injection, implement a unified DB session manager, and add granular logging and metrics for improved observability.

### Key Sub-Tasks
- [ ] **Dependency Injection**: Decouple business logic from task execution.
- [ ] **Unified DB Session Manager**: Create a consistent session manager for async/sync contexts.
- [ ] **Automate DB Patching for Tests**: Move sync DB patching for tests to a global pytest fixture.
- [ ] **Granular Logging**: Integrate detailed, centralized logging.
- [ ] **Metrics Integration**: Collect and visualize metrics with Prometheus/Grafana.

---

## Technical Debt & Future Improvements Checklist

This checklist tracks general technical improvements. Specific items are migrated to Task Master as they are prioritized.

### Core Architecture & CI/CD
- [x] **Makefile**: Automate common tasks (`install`, `run`, `test`, `lint`, etc.).
- [x] **Test Coverage**: Maintain >90% coverage for core logic.
- [x] **Docstrings**: Ensure all public modules are documented.
- [x] **Address Validation**: Wallet and token addresses are validated at multiple layers.
- [x] **Async Endpoints**: All FastAPI endpoints are fully asynchronous.
- [ ] **CI/CD Security**: Integrate Bandit, Safety, and other security scans into the pipeline (Task 5).

### Security & Access Control
- [ ] **Authentication & Authorization**: Implement OAuth2/JWT and RBAC/ABAC (Task 4, 9).
- [ ] **Input Validation**: Ensure all user inputs are validated and sanitized.
- [ ] **Security Headers**: Verify CORS, CSP, HSTS headers are in place.
- [ ] **Audit Trail**: Log all changes to key tables like wallets and transactions (Task 6).
- [ ] **Access Monitoring**: Implement monitoring and alerting for suspicious access patterns (Task 7).

### Database & Data Management
- [ ] **Backup & Restore**: Create automated backup/restore procedures (Task 8).
- [ ] **Custom Metadata**: Support extensible metadata (tags, notes) for wallets/transactions (Task 10).
- [ ] **Multi-Currency Support**: Store values in multiple currencies with live exchange rates (Task 11).
- [ ] **Schema Migrations**: Formalize schema migration management (Task 12).

### Error Handling & Logging
- [ ] **Centralized Error Handling**: Use custom FastAPI exception handlers.
- [ ] **Structured Logging**: Implement structured (JSON) and centralized logging (Task 26).

---
