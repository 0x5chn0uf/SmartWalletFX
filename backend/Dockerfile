# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system deps including curl for health checks
RUN apt-get update && apt-get install -y build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install --verbose .[dev]

COPY . /app

CMD ["sh", "-c", "python -c 'from app.main import app; print(\"App import successful\")' && uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level debug"] 