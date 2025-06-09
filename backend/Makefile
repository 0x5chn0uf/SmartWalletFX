# Makefile pour backend FastAPI

.PHONY: install run test lint format coverage bandit safety clean

install:
	pip install -r requirements/base.txt

install-dev:
	pip install -r requirements/dev.txt

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

test:
	pytest --cov=app --cov-report=term-missing

lint:
	ruff check app tests
	black --check app tests
	isort --check-only app tests
	flake8 app tests --exclude=venv,tests
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