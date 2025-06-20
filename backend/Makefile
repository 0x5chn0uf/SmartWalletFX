# Makefile pour backend FastAPI

.DEFAULT_GOAL := help

# -----------------------------------------------------------------------------
# Backend Makefile – FastAPI service helpers
# -----------------------------------------------------------------------------
#  • Run `make help` to list available commands.
#  • Targets are organised by domain (setup, quality, tests, db, runtime, etc.).
# -----------------------------------------------------------------------------

# Directories / files
COMPOSE_FILE := ../docker-compose.db.yml

# Tools & env
PYTHON := python
PIP := pip
TEST_ENV := BCRYPT_ROUNDS=4

# -----------------------------------------------------------------------------
# Utility – list all targets and one-line descriptions
# -----------------------------------------------------------------------------
help: ## Show this help
	@grep -E '^[a-zA-Z0-9_\-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' | sort

# -----------------------------------------------------------------------------
# Installation / setup
# -----------------------------------------------------------------------------
install: ## Install runtime dependencies
	$(PIP) install -r requirements/base.txt

install-dev: ## Install dev & test dependencies
	$(PIP) install -r requirements/dev.txt

install-perf: ## Install performance-testing deps
	$(PIP) install -r requirements/perf.txt

# -----------------------------------------------------------------------------
# Linting & formatting
# -----------------------------------------------------------------------------
lint: ## Run ruff, black-check, isort-check, flake8 & mypy
	ruff check app tests
	black --check app tests
	isort --check-only app tests
	flake8 app
	mypy app

format: ## Auto-format with black & isort
	black app tests
	isort app tests

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

test-perf: ## Run performance-marked tests
	$(TEST_ENV) pytest -m performance $(TEST_FLAGS)

coverage: ## Generate HTML coverage report
	pytest --cov=app --cov-report=html

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

locust-smoke: ## Run Locust smoke test (100 users, 30s)
	locust -f locustfile.py --headless -u 100 -r 20 -t 30s -H http://localhost:8000 --csv smoke --csv-full-history --exit-code-on-error 0
	$(PYTHON) scripts/check_locust_fail_ratio.py smoke 0.01

# -----------------------------------------------------------------------------
# Alembic / database targets
# -----------------------------------------------------------------------------
db-start: ## Start Postgres dev & Redis containers
	docker compose -f $(COMPOSE_FILE) up -d postgres-dev redis

db-test: ## Start Postgres test container
	docker compose -f $(COMPOSE_FILE) up -d postgres-test

db-down: ## Stop & remove DB containers & volumes
	docker compose -f $(COMPOSE_FILE) down -v

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
	rm -rf __pycache__ .pytest_cache .coverage htmlcov
	find . -type d -name '__pycache__' -exec rm -rf {} +

.PHONY: help install install-dev install-perf lint format bandit safety \
	test test-perf coverage run serve serve-stop celery-worker celery-beat \
	db-start db-test db-down alembic-upgrade db-migrate locust-smoke clean