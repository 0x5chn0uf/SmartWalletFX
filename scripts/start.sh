#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# start.sh – Developer helper to spin up the full SmartWalletFX stack
# -----------------------------------------------------------------------------
# Usage:
#   ./scripts/start.sh            # builds images & starts containers in background
#   STACK_LOGS=1 ./scripts/start.sh  # tail logs after startup
# -----------------------------------------------------------------------------
set -euo pipefail

# Ensure we run from repo root regardless of where the script is executed
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

# Copy env template if .env is missing
if [[ ! -f .env ]]; then
  echo "[start.sh] .env not found. Copying .env.example -> .env"
  cp .env.example .env
fi

# Start the stack
echo "[start.sh] Starting SmartWalletFX containers..."
docker compose up -d --build

echo "[start.sh] Containers are starting. Current status:"
docker compose ps

# Optionally tail logs
if [[ "${STACK_LOGS:-0}" == "1" ]]; then
  echo "[start.sh] Tailing container logs (Ctrl+C to stop)..."
  docker compose logs -f --tail=100
fi