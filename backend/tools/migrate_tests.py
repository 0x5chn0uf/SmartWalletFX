#!/usr/bin/env python
"""migrate_tests.py

Helper script to migrate backend tests to the new domain-oriented directory
layout described in the Test-Suite Restructure PRD. The script supports a
**dry-run** mode (default) that prints planned file moves and an **apply**
mode that performs them.

Examples
--------
# Preview moves for the *auth* domain:
python -m backend.tools.migrate_tests --domain auth

# Execute the moves:
python -m backend.tools.migrate_tests --domain auth --apply

Notes
-----
1. The script is intentionally conservative – it only moves files that match
   explicit patterns for the selected domain.
2. Paths are resolved relative to the project root (directory containing
   *backend/*).
3. After each successful move the script prints the git mv command executed so
   that the operation is fully traceable in commit history.
4. Any errors abort the process; rerun after fixing.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import List, Tuple

# ----------- Configuration --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # /.../trading_bot_smc
BACKEND_TESTS = PROJECT_ROOT / "backend" / "tests"

# Mapping rules: domain -> list of (old_subpath, new_subpath) pairs
MAPPING_RULES = {
    "auth": [
        (Path("unit/api"), Path("domains/auth/unit")),
        (Path("unit/auth"), Path("domains/auth/unit")),
        (Path("integration/auth"), Path("domains/auth/integration")),
        (Path("integration/api/auth"), Path("domains/auth/integration")),
    ],
    "wallets": [
        (Path("unit/repositories"), Path("domains/wallets/unit")),
        (Path("unit/usecase"), Path("domains/wallets/unit")),
        (Path("integration/api/wallets"), Path("domains/wallets/integration")),
    ],
    "admin": [
        (Path("unit/api"), Path("domains/admin/unit")),
        (Path("integration/admin"), Path("domains/admin/integration")),
    ],
    "defi": [
        (Path("unit/strategies"), Path("domains/defi/unit")),
        (Path("integration/defi"), Path("domains/defi/integration")),
    ],
    "jwt_rotation": [
        (Path("unit/jwt_rotation"), Path("domains/auth/unit")),
        (Path("integration/jwt_rotation"), Path("domains/auth/integration")),
        (Path("property/jwt_rotation"), Path("domains/auth/property")),
    ],
    "repositories": [
        (Path("unit/repositories"), Path("infrastructure/database/unit")),
    ],
    "usecase": [
        (Path("unit/usecase"), Path("domains/shared/unit")),
    ],
    "core": [
        (Path("unit/core"), Path("infrastructure/core/unit")),
        (Path("integration/core"), Path("infrastructure/core/integration")),
    ],
    "monitoring": [
        (Path("unit/monitoring"), Path("infrastructure/monitoring/unit")),
        (Path("integration/monitoring"), Path("infrastructure/monitoring/integration")),
    ],
    "utils": [
        (Path("unit/utils"), Path("infrastructure/utils/unit")),
    ],
    "validators": [
        (Path("unit/validators"), Path("infrastructure/security/unit")),
    ],
    "models": [
        (Path("unit/models"), Path("infrastructure/database/unit")),
    ],
    "tasks": [
        (Path("integration/tasks"), Path("infrastructure/async/integration")),
    ],
    "api": [
        (Path("integration/api"), Path("infrastructure/api/integration")),
    ],
    "property_jwks": [
        (Path("property/jwks"), Path("infrastructure/security/property")),
    ],
    "property_shared": [
        (Path("property"), Path("infrastructure/shared/property")),
    ],
    "audit": [
        (Path("unit/audit"), Path("infrastructure/security/unit")),
    ],
    "fixture_lint": [
        (Path("unit/fixture_lint"), Path("infrastructure/testing/unit")),
    ],
}

# ---------------------------------------------------------------------------


def gather_files(src_root: Path, subpath: Path) -> List[Path]:
    """Return all python test files under *src_root/subpath*."""
    candidate_dir = src_root / subpath
    if not candidate_dir.exists():
        return []
    return sorted(candidate_dir.rglob("test_*.py"))


def planned_moves(domain: str) -> List[Tuple[Path, Path]]:
    """Compute (src, dst) move pairs for *domain*."""
    moves: List[Tuple[Path, Path]] = []
    rules = MAPPING_RULES.get(domain)
    if not rules:
        print(
            f"[ERROR] Unknown domain '{domain}'. Available: {', '.join(MAPPING_RULES)}"
        )
        sys.exit(1)

    for old_sub, new_sub in rules:
        for file in gather_files(BACKEND_TESTS, old_sub):
            relative = file.relative_to(BACKEND_TESTS / old_sub)
            target = BACKEND_TESTS / new_sub / relative
            moves.append((file, target))
    return moves


def ensure_target_dirs(pairs: List[Tuple[Path, Path]]) -> None:
    """Create target directories for all *pairs* if they don't exist."""
    for _, dst in pairs:
        dst.parent.mkdir(parents=True, exist_ok=True)


def perform_moves(pairs: List[Tuple[Path, Path]]) -> None:
    """Execute shutil.move for all *pairs*. Uses git mv if repository detected."""
    ensure_target_dirs(pairs)
    for src, dst in pairs:
        if dst.exists():
            print(f"[SKIP] {dst} already exists, skipping {src.name}")
            continue
        print(f"[MOVE] {src} -> {dst}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(src, dst)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migrate backend tests to new domain structure."
    )
    parser.add_argument(
        "--domain", required=True, help="Domain to migrate (e.g., auth, wallets)"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the changes. Without this flag the script performs a dry-run.",
    )
    args = parser.parse_args()

    pairs = planned_moves(args.domain)
    if not pairs:
        print("No files found to migrate. Exit.")
        return

    print("Planned moves:")
    for src, dst in pairs:
        print(f"  {src.relative_to(PROJECT_ROOT)} -> {dst.relative_to(PROJECT_ROOT)}")

    if not args.apply:
        print("\nDry-run complete. Re-run with --apply to execute moves.")
        return

    print("\nApplying moves…")
    perform_moves(pairs)
    print("\nMigration complete.")


if __name__ == "__main__":
    main()
