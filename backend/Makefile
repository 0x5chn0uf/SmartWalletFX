# Backend Makefile – FastAPI service helpers

.DEFAULT_GOAL := help

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
COMPOSE_FILE_DEV  ?= ../docker-compose.yml
COMPOSE_FILE_TEST ?= docker-compose.test.yml
PYTHON := python
PIP := pip

# -----------------------------------------------------------------------------
# Help
# -----------------------------------------------------------------------------
help: ## Show this help
	@grep -E '^[a-zA-Z0-9_\-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' | sort

# -----------------------------------------------------------------------------
# Installation
# -----------------------------------------------------------------------------
install: ## Install runtime dependencies
	$(PIP) install -e .

install-dev: ## Install dev & test dependencies
	$(PIP) install -e ".[dev]"

# -----------------------------------------------------------------------------
# Code Quality
# -----------------------------------------------------------------------------
lint: ## Run all linting checks
	ruff check app tests
	black --check app tests
	isort --check-only app tests
	flake8 app

format: ## Auto-format code
	black app tests migrations
	isort app tests migrations

bandit: ## Security scan
	bandit -r app -ll -ii -f txt

safety: ## Dependency vulnerability check
	safety check

# -----------------------------------------------------------------------------
# Testing
# -----------------------------------------------------------------------------
test: ## Run unit tests only (fast, SQLite) - default for development
	pytest -m unit -v
	@$(MAKE) clean

test-quiet: ## Run unit tests with minimal output (TOKEN-EFFICIENT)
	pytest -q -rfE --tb=line --no-header --disable-warnings --color=no --maxfail=15 -m unit
	@$(MAKE) clean

test-unit: ## Unit tests only (fast, SQLite, parallel)
	pytest -n auto --dist=worksteal -m unit -v
	@$(MAKE) clean

test-integration: ## Integration tests only (PostgreSQL + Docker)
	@$(MAKE) db-test
	@env TEST_DB_URL=postgresql+asyncpg://testuser:testpass@localhost:55432/test_smartwallet pytest -m integration -v
	@$(MAKE) db-stop
	@$(MAKE) clean

test-all: ## Run ALL tests (unit + integration) with PostgreSQL - for CI/CD
	@$(MAKE) db-test
	@env TEST_DB_URL=postgresql+asyncpg://testuser:testpass@localhost:55432/test_smartwallet pytest -v
	@$(MAKE) db-stop
	@$(MAKE) clean

test-all-cov: ## Run ALL tests with coverage and XML report - for CI/CD
	@$(MAKE) db-test
	@env TEST_DB_URL=postgresql+asyncpg://testuser:testpass@localhost:55432/test_smartwallet pytest -v --cov=app --cov-report=xml
	@$(MAKE) db-stop
	@$(MAKE) clean

test-cov: ## Generate coverage report
	pytest -v --cov=app --cov-report=term-missing
	@$(MAKE) clean

test-profile: ## Profile test performance
	pytest --durations=20 --tb=short -v
	@$(MAKE) clean

# -----------------------------------------------------------------------------
# Development Server
# -----------------------------------------------------------------------------
run: ## Start FastAPI development server
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

serve: ## Start services and FastAPI with health check
	@$(MAKE) -s db-start || true
	pkill -f uvicorn || true
	uvicorn app.main:app > uvicorn.log 2>&1 &
	@echo "Waiting for FastAPI to become healthy..."
	@set -e; for i in $$(seq 1 15); do \
	  if curl -s http://localhost:8000/health > /dev/null; then \
	    echo "FastAPI server ready on http://localhost:8000"; exit 0; \
	  fi; echo "[serve] attempt $$i: not ready"; sleep 2; done; \
	cat uvicorn.log; echo "Server failed to start"; exit 1

serve-stop: ## Stop background FastAPI server
	pkill -f uvicorn || true

# -----------------------------------------------------------------------------
# Background Services
# -----------------------------------------------------------------------------
celery-worker: ## Start Celery worker
	celery -A app.celery_app.celery worker --loglevel=info

celery-beat: ## Start Celery beat scheduler
	celery -A app.celery_app.celery beat --loglevel=info

# -----------------------------------------------------------------------------
# Database Management
# -----------------------------------------------------------------------------
db-start: ## Start development database services
	docker compose -f $(COMPOSE_FILE_DEV) up -d postgres-dev redis

db-test: ## Start test database services
	docker compose -f $(COMPOSE_FILE_TEST) up -d postgres-test redis-test
	@echo "Waiting for test services to be ready..."
	@sleep 10

db-stop: ## Stop all database services
	docker compose -f $(COMPOSE_FILE_DEV) down -v
	docker compose -f $(COMPOSE_FILE_TEST) down -v || true

db-migrate: ## Apply database migrations
	alembic upgrade head

db-rollback: ## Rollback to previous migration
	alembic downgrade -1

db-reset: ## Reset database to base
	alembic downgrade base

# -----------------------------------------------------------------------------
# Cleanup
# -----------------------------------------------------------------------------
clean: ## Remove caches and artifacts
	rm -rf __pycache__ .pytest_cache .coverage htmlcov .coverage.* .ruff_cache .hypothesis .benchmarks uvicorn.log
	find . -type d -name '__pycache__' -exec rm -rf {} +
	$(PYTHON) scripts/cleanup_test_uploads.py

clean-dry: ## Preview files that would be cleaned
	$(PYTHON) scripts/cleanup_test_uploads.py --dry-run

.PHONY: help install install-dev lint format bandit safety \
	test test-quiet test-unit test-integration test-cov test-profile \
	run serve serve-stop celery-worker celery-beat \
	db-start db-test db-stop db-migrate db-rollback db-reset \
	clean clean-dry