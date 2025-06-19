# Makefile pour backend FastAPI

.PHONY: install run test lint format coverage bandit safety clean celery-worker celery-beat alembic-upgrade db-start db-test db-down db-migrate serve locust-smoke

install:
	pip install -r requirements/base.txt

install-dev:
	pip install -r requirements/dev.txt

install-perf:
	pip install -r requirements/perf.txt

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

test:
	BCRYPT_ROUNDS=4 pytest --cov=app --cov-report=term-missing

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

serve:
	# Ensure dev database containers are running
	$(MAKE) -s db-start || true
	# Restart uvicorn without reload for clean logs
	pkill -f uvicorn || true
	uvicorn app.main:app > uvicorn.log 2>&1 &
	@echo "Waiting for FastAPI to become healthy..."
	@set -e; \
	for i in $$(seq 1 15); do \
	  if curl -s http://localhost:8000/health > /dev/null; then \
	    echo "FastAPI server is up and running on http://localhost:8000"; \
	    exit 0; \
	  fi; \
	  echo "[serve] attempt $$i: server not ready yet"; \
	  sleep 2; \
	done; \
	cat uvicorn.log; \
	echo "Server failed to start"; \
	exit 1

locust-smoke:
	locust -f locustfile.py --headless -u 100 -r 20 -t 30s -H http://localhost:8000 --csv smoke --csv-full-history --exit-code-on-error 0
	python scripts/check_locust_fail_ratio.py smoke 0.01