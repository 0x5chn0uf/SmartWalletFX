#!/usr/bin/env python
"""Check Locust CSV stats for failure ratio and exit non-zero if threshold exceeded.

Usage:  python check_locust_fail_ratio.py <csv_prefix> [threshold]
Where <csv_prefix> is the prefix passed to --csv (default smoke_stats),
      threshold    is the max allowed failure ratio (float, default 0.01).

Intended for CI pipelines where Locust is run with --exit-code-on-error 0.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path


def main() -> None:  # noqa: D401
    if len(sys.argv) < 2:
        print(
            "Usage: check_locust_fail_ratio.py <csv_prefix> [threshold]",
            file=sys.stderr,
        )
        sys.exit(2)

    prefix = Path(sys.argv[1]).stem  # remove .csv if provided
    threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 0.01

    stats_file = Path(f"{prefix}_stats.csv")
    if not stats_file.exists():
        print(f"Stats file {stats_file} not found", file=sys.stderr)
        sys.exit(2)

    total_reqs = 0
    total_fails = 0
    with stats_file.open(newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if row["Name"] == "Aggregated":
                total_reqs = int(row["# requests"].strip())
                total_fails = int(row["# failures"].strip())
                break

    if total_reqs == 0:
        print("No requests recorded", file=sys.stderr)
        sys.exit(1)

    fail_ratio = total_fails / total_reqs
    print(f"Locust fail ratio: {fail_ratio:.4f} (threshold {threshold})")
    if fail_ratio > threshold:
        print("❌ Error: failure ratio above threshold", file=sys.stderr)
        sys.exit(1)

    print("✅ OK: failure ratio within threshold")


if __name__ == "__main__":
    main()
