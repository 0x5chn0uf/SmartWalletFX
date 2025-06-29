# Contributing Guide

Thanks for considering contributing to **SmartWalletFX**! This document explains how to set up the project locally, with a special focus on using _separate_ PostgreSQL databases for **development** and **test** environments.

---

## Table of Contents

1. Getting Started
2. Development Database Setup
3. Test Database Workflow
4. Running Database Migrations (Alembic)
5. Quick-Reference Commands & Makefile Targets
6. Troubleshooting

---

## 1. Getting Started

### Prerequisites

- Docker & Docker Compose v2
- Python 3.12+
- Node.js 20.19+

Clone the repo and copy environment variables:

```bash
git clone https://github.com/0x5chn0uf/smartwalletfx.git
cd smartwalletfx
cp .env.example .env  # edit values as needed
```

---

## 2. Development Database Setup

We use SQLite by default; **no database container is required**.  
However, a `docker-compose.db.yml` file is included with Postgres + Redis services for developers who prefer Postgres locally **or** for the future migration.

### Using built-in SQLite (recommended for quick start)

Simply rely on the default URLs in `.env` / `backend/env.example`:

```env
DATABASE_URL=sqlite:///./smartwallet_dev.db
```

### Using Postgres instead (optional)

```bash
# Start Postgres & Redis containers
docker compose -f docker-compose.db.yml up -d postgres-dev redis

# Point the backend to Postgres
export DATABASE_URL=postgresql://devuser:devpass@localhost:5432/smartwallet_dev

# Apply migrations
cd backend && alembic upgrade head
```

> **Tip:** The provided Makefile has `make db-start` / `make db-down` helpers that wrap these commands.

---

## 3. Test Database Workflow

Automated tests require a **clean** database instance every run. Our pytest fixtures spin up **postgres-test** (port 55432) on demand:

```bash
docker compose -f docker-compose.db.yml up -d postgres-test

# run the tests (uses TEST_DATABASE_URL)
cd backend
TEST_DATABASE_URL=postgresql://testuser:testpass@localhost:55432/smartwallet_test make test
```

The key fixture lives in `backend/tests/conftest.py` and creates a new temporary database schema before each test session, ensuring tests remain idempotent.

Environment variable:

```
TEST_DATABASE_URL=postgresql://testuser:testpass@localhost:55432/smartwallet_test
```

### Automatic Teardown

After the test run, pytest triggers `docker compose stop postgres-test` via a session-finish hook. If you need to clean up manually:

```bash
docker compose -f docker-compose.db.yml down -v postgres-test
```

---

## 4. Running Database Migrations (Alembic)

Generate a migration after editing models:

```bash
cd backend
alembic revision --autogenerate -m "short description"
```

Apply migrations (dev DB):

```bash
make db-migrate
```

Apply migrations to the **test** database (rarely needed manually):

```bash
TEST_DATABASE_URL=postgresql://testuser:testpass@localhost:55432/smartwallet_test alembic upgrade head
```

---

## 5. Quick-Reference Commands & Makefile Targets

| Purpose                   | Command                                                            |
| ------------------------- | ------------------------------------------------------------------ |
| Start dev services        | `docker compose -f docker-compose.db.yml up -d postgres-dev redis` |
| Stop dev DB               | `docker compose -f docker-compose.db.yml stop postgres-dev`        |
| Start test DB             | `docker compose -f docker-compose.db.yml up -d postgres-test`      |
| Run tests                 | `TEST_DATABASE_URL=… make test`                                    |
| Create migration          | `alembic revision --autogenerate -m "msg"`                         |
| Apply migrations          | `make db-migrate`                                                  |
| Destroy all DB containers | `docker compose -f docker-compose.db.yml down -v`                  |

The **backend/Makefile** already includes helpful shortcuts:

```make
make db-start      # starts postgres-dev using docker-compose
make db-test       # starts postgres-test
make db-migrate    # upgrade dev DB to latest head
```

---

## 6. Troubleshooting

| Symptom                                  | Fix                                                                          |
| ---------------------------------------- | ---------------------------------------------------------------------------- |
| `psycopg2.OperationalError` connecting   | Verify `postgres-dev` is running and `DATABASE_URL` is correct               |
| Tests hang on DB step                    | Ensure no process already binds to port 55432                                |
| Alembic migration fails with permissions | Check Postgres user / password in `.env` and container logs                  |
| Old data should be wiped                 | `docker compose -f docker-compose.db.yml down -v postgres-dev postgres-test` |

Feel free to open an issue or ping the maintainers if you hit problems not covered here. Happy hacking! :rocket:
