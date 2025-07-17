# Makefile pour backend FastAPI

.DEFAULT_GOAL := help

# -----------------------------------------------------------------------------
# Backend Makefile – FastAPI service helpers
# -----------------------------------------------------------------------------
#  • Run `make help` to list available commands.
#  • Targets are organised by domain (setup, quality, tests, db, runtime, etc.).
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Docker Compose files – separated for dev & test stacks
# -----------------------------------------------------------------------------

COMPOSE_FILE_DEV  ?= ../docker-compose.yml
COMPOSE_FILE_TEST ?= ../docker-compose.test.yml

# Tools & env
PYTHON := python
PIP := pip
TEST_ENV := BCRYPT_ROUNDS=4 TEST_DB_URL=

# -----------------------------------------------------------------------------
# Utility – list all targets and one-line descriptions
# -----------------------------------------------------------------------------
help: ## Show this help
	@grep -E '^[a-zA-Z0-9_\-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' | sort

# -----------------------------------------------------------------------------
# Installation / setup
# -----------------------------------------------------------------------------
install: ## Install runtime dependencies
	$(PIP) install -e .

install-dev: ## Install dev & test dependencies
	$(PIP) install -e ".[dev]"


# -----------------------------------------------------------------------------
# Linting & formatting
# -----------------------------------------------------------------------------
lint: ## Run ruff, black-check, isort-check & flake8
	ruff check app tests
	black --check app tests
	isort --check-only app tests
	flake8 app

format: ## Auto-format with black & isort
	black app tests migrations
	isort app tests migrations

bandit: ## Static security scan
	bandit -r app -ll -ii -f txt

safety: ## Dependency vulnerability scan
	safety check

# -----------------------------------------------------------------------------
# Tests & coverage
# -----------------------------------------------------------------------------
TEST_FLAGS := -v

test: ## Run pytest suite
	$(TEST_ENV) pytest $(TEST_FLAGS)
	$(MAKE) clean

test-perf: ## Run performance-marked tests
	$(TEST_ENV) pytest -m performance $(TEST_FLAGS)

test-cov: ## Generate HTML coverage report
	$(TEST_ENV) pytest $(TEST_FLAGS) --cov=app --cov-report=term-missing

test-quiet:
	$(TEST_ENV) pytest -q -rfE --tb=line --no-header --disable-warnings --color=no --maxfail=15
# -----------------------------------------------------------------------------
# Runtime helpers
# -----------------------------------------------------------------------------
run: ## Start uvicorn (0.0.0.0:8000)
	uvicorn app.main:app --host 0.0.0.0 --port 8000

serve: ## Start DB (if needed) then uvicorn with readiness probe
	@$(MAKE) -s db-start || true
	pkill -f uvicorn || true
	uvicorn app.main:app > uvicorn.log 2>&1 &
	@echo "Waiting for FastAPI to become healthy...";
	@set -e; for i in $$(seq 1 15); do \
	  if curl -s http://localhost:8000/health > /dev/null; then \
	    echo "FastAPI server ready on http://localhost:8000"; exit 0; \
	  fi; echo "[serve] attempt $$i: not ready"; sleep 2; done; \
	cat uvicorn.log; echo "Server failed to start"; exit 1

serve-stop: ## Stop the background uvicorn process
	pkill -f uvicorn || true

celery-worker: ## Start Celery worker
	celery -A app.celery_app.celery worker --loglevel=info

celery-beat: ## Start Celery beat scheduler
	celery -A app.celery_app.celery beat --loglevel=info

# -----------------------------------------------------------------------------
# Alembic / database targets
# -----------------------------------------------------------------------------
# Development database stack (postgres-dev + redis)
db-start: ## Start Postgres dev & Redis containers
	docker compose -f $(COMPOSE_FILE_DEV) up -d postgres-dev redis

# Test database stack (postgres-test + redis)
db-test: ## Start Postgres test container
	docker compose -f $(COMPOSE_FILE_TEST) up -d postgres-test redis

db-down: ## Stop & remove DB containers & volumes
	docker compose -f $(COMPOSE_FILE_DEV) down -v
	docker compose -f $(COMPOSE_FILE_TEST) down -v || true

alembic-rollback: ## Rollback DB to previous Alembic revision
	PYTHONPATH=. alembic downgrade -1

db-rollback: ## Rollback DB to previous migration (alias to alembic-rollback)
	$(MAKE) alembic-rollback
alembic-rollback-all: ## Rollback DB to base (all migrations)
	PYTHONPATH=. alembic downgrade base

db-rollback-all: ## Rollback DB to base (alias to alembic-rollback-all)
	$(MAKE) alembic-rollback-all


alembic-upgrade: ## Upgrade DB to latest Alembic head
	PYTHONPATH=. alembic upgrade head

# Uses DATABASE_URL from environment or .env
# Example: make db-migrate DATABASE_URL=postgresql://user:pass@localhost:5432/app_dev

db-migrate: ## Apply latest migrations (alias to alembic-upgrade)
	$(MAKE) alembic-upgrade

# -----------------------------------------------------------------------------
# House-keeping
# -----------------------------------------------------------------------------
clean: ## Remove caches & artefacts
	rm -rf __pycache__ .pytest_cache .coverage htmlcov .coverage.* .ruff_cache .hypothesis .benchmarks uvicorn.log
	find . -type d -name '__pycache__' -exec rm -rf {} +

.PHONY: help install install-dev install-s3 install-perf lint format bandit safety \
	test test-perf coverage run serve serve-stop celery-worker celery-beat \
	db-start db-test db-down alembic-upgrade db-migrate clean