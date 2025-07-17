# SmartWalletFX – Backend Architecture

> **Scope**: This document describes the architecture of the SmartWalletFX backend (FastAPI + async stack).

---

## 1  High‑Level Overview

* **Pattern**: Hexagonal (Ports & Adapters) reinforced by explicit **dependency injection**.
* **Language & Runtime**: Python 3.12, fully async.
* **Primary Services**

  * **FastAPI** web layer (HTTP & WebSocket)
  * **PostgreSQL** (async SQLAlchemy 2.0) for persistence
  * **Redis** for caching & Celery message broker
  * **Celery** for background tasks
* **Non‑Backend Components** (out of repo)

  * **React + TradingView** front‑end SPA
  * **Blockchain nodes** (Infura / Alchemy) queried through **Web3.py**

Diagram‑level summary (textual):

```
             ┌────────────┐   Commands / Queries   ┌────────────┐
   HTTP ───▶ │  Endpoints │ ──────────────────────▶│  Usecases  │
             └────────────┘                        └────────────┘
                    ▲                                     │
                    │ DTOs / Schemas                      │ domain ops
                    │                                     ▼
             ┌────────────┐                        ┌────────────┐
             │  Services  │◀── adapters / ports ───│Repositories│
             └────────────┘                        └────────────┘
                    ▲                                     │
                    │ async DB / Redis / Web3             │ SQL / RPC
                    ▼                                     ▼
               External Systems (PostgreSQL, Redis, EVM chains)
```

---

## 2  Layer Breakdown

| Layer            | Package / Path       | Responsibility                                                         |
| ---------------- | -------------------- | ---------------------------------------------------------------------- |
| **Core**         | `app/core/`          | Cross‑cutting infra: config, logging, error handling, database engines |
| **Repositories** | `app/repositories/`  | Data access logic isolated behind interfaces                           |
| **Usecases**     | `app/usecase/`       | Business rules; orchestrate repositories & services                    |
| **Endpoints**    | `app/api/endpoints/` | Transport layer (HTTP/WebSocket) – translate DTO⇄Domain                |
| **Services**     | `app/services/`      | Cross‑cutting helpers (auth, email, OAuth)                             |
| **Tasks**        | `app/tasks/`         | Celery job definitions                                                 |
| **Domain**       | `app/domain/`        | Pydantic models & value objects                                        |

### 2.1 Dependency Injection

`app/di.py` exposes a \`\` that lazily instantiates singletons on first request.  All layers request their collaborators through the container; no module‑level globals remain.  During testing the container is overridden with fakes/mocks.

### 2.2 Application Factory

`app/main.py` implements `ApplicationFactory`, responsible for:

* creating the FastAPI instance
* wiring middlewares / CORS / exception handlers
* boot‑strapping DIContainer on startup & shutdown hooks

---

## 3  Refactoring Roadmap (Timeline)

| Phase | Status         | Description                                                     |
| ----- | -------------- | --------------------------------------------------------------- |
| 1     | ✅ Done         | Core infra classes converted to DI                              |
| 2     | ✅ Done         | Repositories DI‑enabled                                         |
| 3     | ✅ Done         | Usecases DI‑enabled                                             |
| 4     | ✅ Done         | API endpoints converted to class singletons                     |
| 5     | ✅ Done         | Helper utilities DI‑enabled                                     |
| 6     | 🔄 In progress | **Test suite refactor** – standard fixtures, DI‑aware factories |

---

## 4  Directory Structure (level 2)

```
backend/
├── app/
│   ├── api/endpoints/     # Transport layer
│   ├── core/             # Infrastructure
│   ├── repositories/     # Data mappers
│   ├── services/         # Cross‑cutting
│   ├── usecase/          # Business logic
│   ├── utils/            # Helpers
│   ├── domain/           # Schemas & value objects
│   ├── tasks/            # Celery jobs
│   ├── validators/       # Input validation rules
│   ├── di.py            # DI container
│   └── main.py          # App factory
├── tests/               # Unit, integration, perf
├── migrations/          # Alembic scripts
├── Makefile            # Dev commands
└── pyproject.toml      # Tooling & deps
```

---

## 5  Key Technology Decisions

| Concern             | Choice & Rationale                                                           |
| ------------------- | ---------------------------------------------------------------------------- |
| **Web framework**   | FastAPI + ASGI – best async performance, OpenAPI out of the box              |
| **ORM**             | SQLAlchemy 2.0 async – maturity + type hints                                 |
| **Background jobs** | Celery 5 + Redis – simple, reliable, monitored via Flower                    |
| **Security**        | JWT (RS256) with key rotation; RBAC enforced in endpoints                    |
| **DI**              | Home‑grown container – avoids external runtime deps & keeps startup explicit |

---

## 6  Performance Notes

* Endpoints are fully async; IO‑bound latency hidden behind `await`.
* Connection pools tuned (PostgreSQL: 5↔30, Redis: 10).
* Hot‑path queries cached for 60 s in Redis.
* Prometheus metrics scraped every 15 s; Grafana dashboard available.

---

## 7  Security Posture

* Static analysis: **ruff**, **bandit**, **safety** in CI.
* Strict CORS & rate limiting on auth routes.
* Bcrypt‑hashed passwords; env‑rotated secrets.
* SQL injection mitigated via SQLAlchemy Core & Pydantic validation.

---

## 8  Testing Strategy

* **Unit**: repo & usecase isolation via DI mocks.
* **Integration**: spin‑up PostgreSQL + Redis containers (docker‑compose) per job.
* **Performance**: `-m performance` markers; run nightly.
* **Coverage gate**: 90 % lines / 80 % branches.

---

## 9  How to Extend

1. Add new repository class under `app/repositories/…`.
2. Register it inside `DIContainer.register()`.
3. Inject into a usecase via constructor.
4. Expose via endpoint method.

No global state; unit tests mock at any seam.

---

*Last updated: 17 July 2025*
