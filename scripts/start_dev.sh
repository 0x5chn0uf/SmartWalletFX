#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
# Convenience script for local development.
#   1. Starts Postgres + Redis via docker-compose (in detached mode)
#   2. Launches the FastAPI backend with hot-reload
#   3. Launches the React/Vite frontend
#
#   Usage: ./scripts/start_dev.sh
# -----------------------------------------------------------------------------

# Define helper to check if a command exists
command -v docker compose >/dev/null 2>&1 || {
    echo >&2 "docker-compose is required but not installed. Aborting."; exit 1;
}

# 1. Start infrastructure services (runs in background, returns immediately)

# Load environment variables from .env if present so backend running on host sees DATABASE_URL
if [ -f .env ]; then
  echo "▶ Loading environment variables from .env"
  set -a
  source .env
  set +a
fi

echo "▶ Starting mailhog, PostgreSQL & Redis containers…"
docker compose up -d postgres-dev redis mailhog

# 2. Start backend (hot-reload) in a new terminal tab/window if available.
#    Fallback: run in background so the script continues to frontend.

echo "▶ Starting FastAPI backend (uvicorn --reload)…"
( cd backend && make serve ) &

# 3. Start frontend dev server

echo "▶ Starting React dev server…"
( cd frontend && npm run dev )

# When the user stops the frontend (Ctrl-C), propagate shutdown.

echo "▲ Dev environment stopped"
