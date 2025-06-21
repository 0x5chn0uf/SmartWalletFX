"""Prometheus metrics for backup/restore operations."""
from __future__ import annotations

import os

from prometheus_client import Counter, Histogram

_LABELS = {
    "env": os.getenv("ENVIRONMENT", "dev"),
}

BACKUP_TOTAL = Counter(
    "db_backup_total",
    "Total number of backup attempts",
    labelnames=list(_LABELS.keys()),
)
BACKUP_FAILED_TOTAL = Counter(
    "db_backup_failed_total",
    "Number of failed backup attempts",
    labelnames=list(_LABELS.keys()),
)
BACKUP_DURATION_SECONDS = Histogram(
    "db_backup_duration_seconds",
    "Duration of successful backups in seconds",
    labelnames=list(_LABELS.keys()),
)
BACKUP_SIZE_BYTES = Histogram(
    "db_backup_size_bytes",
    "Size of successful backup files in bytes",
    labelnames=list(_LABELS.keys()),
    buckets=(
        1024,
        10 * 1024,
        100 * 1024,
        1024 * 1024,
        10 * 1024 * 1024,
        100 * 1024 * 1024,
    ),
)

# Provide pre-labelled instances for convenience
BACKUP_TOTAL_L = BACKUP_TOTAL.labels(**_LABELS)
BACKUP_FAILED_TOTAL_L = BACKUP_FAILED_TOTAL.labels(**_LABELS)
BACKUP_DURATION_SECONDS_L = BACKUP_DURATION_SECONDS.labels(**_LABELS)
BACKUP_SIZE_BYTES_L = BACKUP_SIZE_BYTES.labels(**_LABELS)
