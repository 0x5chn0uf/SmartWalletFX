# Makefile pour backend FastAPI

.PHONY: install run test lint format coverage bandit safety clean celery-worker celery-beat alembic-upgrade db-start db-test db-down db-migrate

install:
	pip install -r requirements/base.txt

install-dev:
	pip install -r requirements/dev.txt

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

test:
	PYTHONPATH=. pytest --cov=app --cov-report=term-missing

lint:
	ruff check app tests
	black --check app tests
	isort --check-only app tests
	flake8 app
	mypy app

format:
	black app tests
	isort app tests

coverage:
	pytest --cov=app --cov-report=html

bandit:
	bandit -r app -ll -ii -f txt

safety:
	safety check

clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov
	find . -type d -name '__pycache__' -exec rm -rf {} +

celery-worker:
	celery -A app.celery_app.celery worker --loglevel=info

celery-beat:
	celery -A app.celery_app.celery beat --loglevel=info

alembic-upgrade:
	PYTHONPATH=. alembic upgrade head

# --- Database helper targets ---

db-start:
	docker compose -f ../docker-compose.db.yml up -d postgres-dev redis

# Start only the test database (useful in CI or when running tests locally)
db-test:
	docker compose -f ../docker-compose.db.yml up -d postgres-test

# Stop and remove dev/test DB containers & volumes
db-down:
	docker compose -f ../docker-compose.db.yml down -v

# Apply latest Alembic migrations to dev DB
# Uses DATABASE_URL from your .env or defaults to local dev connection
# Example: make db-migrate DATABASE_URL=postgresql://devuser:devpass@localhost:5432/smartwallet_dev

db-migrate:
	PYTHONPATH=. alembic upgrade head