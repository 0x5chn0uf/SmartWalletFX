#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# wait-for-it.sh – Simplified version of the original script by vishnubob
# (https://github.com/vishnubob/wait-for-it) released under the MIT License.
# -----------------------------------------------------------------------------
# Usage:
#   ./scripts/wait-for-it.sh host:port [-t timeout] -- command_to_execute
# -----------------------------------------------------------------------------
set -euo pipefail

HOST_PORT="$1"; shift
HOST="${HOST_PORT%%:*}"
PORT="${HOST_PORT##*:}"

TIMEOUT=30

# Optional flags
if [[ "$1" == "-t" ]]; then
  TIMEOUT="$2"; shift 2
fi

# Optional -- separator
if [[ "$1" == "--" ]]; then
  shift
fi

START_TIME=$(date +%s)
while true; do
  if (echo > /dev/tcp/$HOST/$PORT) &>/dev/null; then
    echo "[wait-for-it] $HOST:$PORT is available"
    break
  fi
  NOW=$(date +%s)
  if (( NOW - START_TIME >= TIMEOUT )); then
    echo "[wait-for-it] Timeout after ${TIMEOUT}s waiting for $HOST:$PORT" >&2
    exit 1
  fi
  sleep 1
done

# Execute the remaining command if provided
if [[ $# -gt 0 ]]; then
  exec "$@"
fi
