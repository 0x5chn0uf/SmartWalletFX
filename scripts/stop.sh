#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# stop.sh – Developer helper to stop and clean the SmartWalletFX stack
# -----------------------------------------------------------------------------
# Usage:
#   ./scripts/stop.sh        # stop containers and preserve volumes
#   PURGE=1 ./scripts/stop.sh  # also remove volumes for a clean slate
# -----------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

echo "[stop.sh] Stopping SmartWalletFX containers..."
docker compose down ${PURGE:+-v}

echo "[stop.sh] Done."
