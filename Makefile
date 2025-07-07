.DEFAULT_GOAL := help

# -----------------------------------------------------------------------------
# Root Makefile – project-wide helper targets
# -----------------------------------------------------------------------------
# Run `make help` (or simply `make`) at the repository root to see a list of the
# most common developer commands. Each target delegates to the corresponding
# backend or frontend command so that contributors can work from a single entry
# point.
# -----------------------------------------------------------------------------

# Directories
BACKEND_DIR := backend
FRONTEND_DIR := frontend

# -----------------------------------------------------------------------------
# Utility – list all targets with descriptions
# -----------------------------------------------------------------------------
help: ## Show this help message
	@grep -E '^[a-zA-Z0-9_\-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' | sort

# -----------------------------------------------------------------------------
# Installation & setup
# -----------------------------------------------------------------------------
setup: setup-backend setup-frontend ## Install Python & Node dependencies

setup-backend: ## Install backend dependencies via backend/Makefile
	$(MAKE) -C $(BACKEND_DIR) install-dev

setup-frontend: ## Install frontend npm dependencies
	cd $(FRONTEND_DIR) && npm ci

cd-back: ## Activate the virtual environment
	cd $(BACKEND_DIR) && source .venv/bin/activate

# -----------------------------------------------------------------------------
# Linting & formatting
# -----------------------------------------------------------------------------
lint: lint-backend lint-frontend ## Run all linters

lint-backend: ## Lint backend code (ruff, black, flake8)
	$(MAKE) -C $(BACKEND_DIR) lint

lint-frontend: ## Lint frontend code (eslint & prettier)
	cd $(FRONTEND_DIR) && npm run lint

format: format-backend ## Auto-format backend (black + isort)

format-backend: ## Format backend code
	$(MAKE) -C $(BACKEND_DIR) format

# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------

test: test-backend test-frontend test-ci ## Run all tests

# Backend tests (pytest + coverage)

test-backend: ## Run backend pytest suite
	$(MAKE) -C $(BACKEND_DIR) test

coverage-backend: ## Generate backend coverage HTML
	$(MAKE) -C $(BACKEND_DIR) coverage

# Frontend tests (Jest)

test-frontend: ## Run frontend Jest suite
	cd $(FRONTEND_DIR) && npx vitest run 

# CI / CD (act)

test-ci: ## Test CI/CD locally with act
	act --list
	act pull_request --container-architecture linux/amd64

# -----------------------------------------------------------------------------
# Development servers
# -----------------------------------------------------------------------------
run-backend: ## Start FastAPI locally with health-check helper
	$(MAKE) -C $(BACKEND_DIR) serve

run-frontend: ## Start React dev server
	cd $(FRONTEND_DIR) && npm run dev

# -----------------------------------------------------------------------------
# Tokens
# -----------------------------------------------------------------------------

build-tokens: ## Generate TypeScript tokens from design-tokens.json via Style Dictionary
	cd $(FRONTEND_DIR) && npm run build:tokens

# -----------------------------------------------------------------------------
# Database helpers (delegated to backend Makefile)
# -----------------------------------------------------------------------------

db-start: ## Start local Postgres & Redis containers
	$(MAKE) -C $(BACKEND_DIR) db-start

db-test: ## Start test database containers
	$(MAKE) -C $(BACKEND_DIR) db-test

db-down: ## Stop & remove DB containers
	$(MAKE) -C $(BACKEND_DIR) db-down

# -----------------------------------------------------------------------------
# Backup helpers – delegate to backend Makefile
# -----------------------------------------------------------------------------

db-backup: ## Delegate to backend/db-backup target
	$(MAKE) -C $(BACKEND_DIR) db-backup $(MAKEFLAGS)

db-restore: ## Delegate to backend/db-restore target
	$(MAKE) -C $(BACKEND_DIR) db-restore $(MAKEFLAGS)

# -----------------------------------------------------------------------------
# Clean & misc
# -----------------------------------------------------------------------------
clean: clean-backend ## Remove temporary files & caches

clean-backend:
	$(MAKE) -C $(BACKEND_DIR) clean

# -----------------------------------------------------------------------------
# Full-stack helper
# -----------------------------------------------------------------------------

start: ## Start full dev stack (DB + backend + frontend)
	bash scripts/start_dev.sh

.PHONY: help setup setup-backend setup-frontend lint lint-backend lint-frontend \
	format format-backend test test-backend test-frontend coverage-backend \
	run-backend run-frontend db-start db-test db-down clean clean-backend \
	db-backup db-restore start 