"""Command-line interface for database backup utilities.

This lightweight CLI exists primarily for developer ergonomics and Makefile
wrappers.  The heavy-lifting is performed by :pymod:`app.utils.db_backup`.

Usage examples
--------------
$ python -m app.cli.db_backup_cli backup --output-dir ./backups
$ # Restore with explicit environment & force flag
$ python -m app.cli.db_backup_cli restore ./backups/20250621_abcdef01.sql.gz \
$     --env staging --force
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable

from app.utils import db_backup  # Lazy import safe for unit tests


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="db-backup-cli",
        description="Database backup / restore helper commands",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # backup sub-command
    backup_parser = subparsers.add_parser("backup", help="Create a DB dump")
    backup_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.cwd(),
        help="Directory to write the dump to (default: current working dir)",
    )
    backup_parser.add_argument(
        "--label",
        type=str,
        default=None,
        help="Optional label to embed in the dump filename",
    )

    # restore sub-command
    restore_parser = subparsers.add_parser("restore", help="Restore a DB dump")
    restore_parser.add_argument(
        "dump_file",
        type=Path,
        help="Path to the .sql or .sql.gz dump to restore",
    )
    restore_parser.add_argument(
        "--env",
        type=str,
        default="development",
        help="Current environment (production, staging, development, test)",
    )
    restore_parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass the production safety guard",
    )

    return parser


def main(argv: list[str] | None = None) -> int:  # pragma: no cover -- direct exit path
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Dispatch table mapping sub-command -> handler
    handlers: dict[str, Callable[[argparse.Namespace], int]] = {
        "backup": _handle_backup,
        "restore": _handle_restore,
    }

    return handlers[args.command](args)


def _handle_backup(ns: argparse.Namespace) -> int:
    try:
        path = db_backup.create_dump(
            ns.output_dir, label=ns.label, compress=True, env=None
        )
        print(path)  # noqa: T201 – simple stdout for CLI
        return 0
    except Exception as exc:  # pragma: no cover
        print(f"Backup failed: {exc}", file=sys.stderr)
        return 1


def _handle_restore(ns: argparse.Namespace) -> int:
    # Safety guard: refuse to restore into production unless --force provided
    env_name: str = ns.env.lower()
    if env_name == "production" and not ns.force:
        print("Refusing to restore into production without --force", file=sys.stderr)
        return 2

    try:
        db_backup.restore_dump(
            ns.dump_file, force=ns.force, target_db_url=None, env=None
        )
        print("Restore completed")  # noqa: T201
        return 0
    except Exception as exc:  # pragma: no cover
        print(f"Restore failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
