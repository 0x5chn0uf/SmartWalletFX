#!/usr/bin/env python3
"""
Migration script for backfilling existing TaskMaster and Serena archives.

This script scans the .taskmaster/memory-bank/ and .serena/memories/ directories
and indexes all existing markdown files into the SQLite database.

Usage:
    python scripts/migrate.py --dry-run
    python scripts/migrate.py --workers 8 --force
    python scripts/migrate.py --directories ".taskmaster/memory-bank/archive,.serena/memories"
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Ensure serena package is importable when executed directly
if __package__ is None or __package__.startswith("__main__"):
    import importlib.util

    root = Path(__file__).resolve().parent.parent
    spec = importlib.util.spec_from_file_location("serena", root / "__init__.py")
    if spec and spec.loader:
        serena_pkg = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(serena_pkg)  # type: ignore
        sys.modules["serena"] = serena_pkg

from serena.infrastructure.database import get_database_path, init_database
from serena.infrastructure.indexer import MemoryIndexer
from serena.services.memory_impl import Memory


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")


def main():
    """Main migration script entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate existing TaskMaster and Serena archives to SQLite index",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without making changes",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-indexing of files that already exist in database",
    )

    parser.add_argument(
        "--directories",
        help="Comma-separated list of directories to scan (overrides defaults)",
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of worker threads for concurrent processing (default: 4)",
    )

    parser.add_argument(
        "--db-path",
        help="Path to SQLite database (default: from SERENA_MEMORY_DB env var)",
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )

    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize database schema before migration",
    )

    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Set database path if provided
        if args.db_path:
            os.environ["SERENA_MEMORY_DB"] = args.db_path

        db_path = get_database_path()

        # Initialize database if requested or if it doesn't exist
        if args.init or not Path(db_path).exists():
            logger.info("Initializing database...")
            init_database(db_path)
            logger.info(f"Database initialized at: {db_path}")

        # Parse directories
        directories = None
        if args.directories:
            directories = [d.strip() for d in args.directories.split(",")]
            logger.info(f"Scanning custom directories: {directories}")
        else:
            logger.info(
                "Scanning default directories: .taskmaster/memory-bank/, .serena/memories/"
            )

        # Create memory instance and indexer
        memory = Memory(db_path=db_path)
        indexer = MemoryIndexer(memory=memory, max_workers=args.workers)

        if args.dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
            # TODO: Implement actual dry run functionality
            print("Dry run functionality not yet implemented")
            return

        # Get initial health status
        initial_health = memory.health()
        logger.info(
            f"Initial state: {initial_health.archive_count} archives, "
            f"{initial_health.embedding_count} embeddings"
        )

        # Perform migration
        logger.info("Starting migration...")
        stats = indexer.scan_directories(
            directories=directories, force_reindex=args.force, show_progress=True
        )

        # Get final health status
        final_health = memory.health()

        # Print results
        print("\n" + "=" * 60)
        print("MIGRATION COMPLETE")
        print("=" * 60)
        print(f"Directories scanned: {stats['directories_scanned']}")
        print(f"Files found: {stats['files_found']}")
        print(f"Files indexed: {stats['files_indexed']}")
        print(f"Files skipped: {stats['files_skipped']}")
        print(f"Files failed: {stats['files_failed']}")
        print()
        print(
            f"Database before: {initial_health.archive_count} archives, "
            f"{initial_health.embedding_count} embeddings"
        )
        print(
            f"Database after:  {final_health.archive_count} archives, "
            f"{final_health.embedding_count} embeddings"
        )
        print(
            f"Net change: +{final_health.archive_count - initial_health.archive_count} archives, "
            f"+{final_health.embedding_count - initial_health.embedding_count} embeddings"
        )
        print()
        print(f"Database location: {db_path}")
        print(f"Database size: {final_health.database_size / (1024*1024):.1f} MB")

        if stats["files_failed"] > 0:
            logger.warning(
                f"{stats['files_failed']} files failed to process. "
                f"Check logs for details."
            )

        logger.info("Migration completed successfully")

    except KeyboardInterrupt:
        print("\nMigration cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
