#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# smoke_test.sh – Validate that the full stack is up & healthy.
# -----------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

# Wait for backend & frontend
"$SCRIPT_DIR/wait-for-it.sh" localhost:8000 -t 60
"$SCRIPT_DIR/wait-for-it.sh" localhost:3000 -t 60

echo "[smoke] Backend ✔ $(curl -s http://localhost:8000/health)"
echo "[smoke] Frontend root status: $(curl -o /dev/null -s -w "%{http_code}" http://localhost:3000)"