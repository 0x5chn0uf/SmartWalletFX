#!/usr/bin/env python3
"""
Database maintenance utilities for the memory bridge.

Provides utilities for:
- WAL checkpoint and optimization
- Database vacuum and cleanup
- Re-embedding old content
- Health monitoring and diagnostics

Usage:
    python scripts/maintenance.py --checkpoint
    python scripts/maintenance.py --vacuum
    python scripts/maintenance.py --reembed --if-stale 180d
    python scripts/maintenance.py --health --detailed
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from serena.infrastructure.database import (
    checkpoint_database,
    get_database_path,
    vacuum_database,
)
from sqlalchemy import text
from serena.services.memory_impl import Memory
from serena.settings import settings


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")


def parse_duration(duration_str: str) -> timedelta:
    """
    Parse duration string like '180d', '7d', '24h' into timedelta.

    Args:
        duration_str: Duration string (e.g., '180d', '7d', '24h')

    Returns:
        timedelta: Parsed duration
    """
    if duration_str.endswith("d"):
        days = int(duration_str[:-1])
        return timedelta(days=days)
    elif duration_str.endswith("h"):
        hours = int(duration_str[:-1])
        return timedelta(hours=hours)
    elif duration_str.endswith("m"):
        minutes = int(duration_str[:-1])
        return timedelta(minutes=minutes)
    else:
        raise ValueError(f"Invalid duration format: {duration_str}")


def cmd_checkpoint(args) -> None:
    """Perform WAL checkpoint and optimization."""
    logger = logging.getLogger(__name__)

    logger.info("Performing WAL checkpoint...")
    checkpoint_database(args.db_path)
    logger.info("WAL checkpoint completed")


def cmd_vacuum(args) -> None:
    """Perform database vacuum."""
    logger = logging.getLogger(__name__)

    # Pre-vacuum backup (optional)
    if settings.maintenance.backup.enable_pre_vacuum_backup:
        backup_dir = Path(settings.maintenance.backup.backup_directory)
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"pre_vacuum_backup_{timestamp}.db"

        from shutil import copyfile

        try:
            logger.info("Performing pre-vacuum backup to %s", backup_path)
            copyfile(args.db_path, backup_path)

            # Clean up old backups
            backups = sorted(backup_dir.glob("pre_vacuum_backup_*.db"), reverse=True)
            if len(backups) > settings.maintenance.backup.max_backup_files:
                for old_backup in backups[settings.maintenance.backup.max_backup_files :]:
                    logger.info("Removing old backup: %s", old_backup)
                    old_backup.unlink()

        except Exception as e:
            logger.error("Pre-vacuum backup failed: %s", e)
            # Do not proceed with vacuum if backup fails
            return

    logger.info("Performing database vacuum...")
    vacuum_database(args.db_path)
    logger.info("Database vacuum completed")


def cmd_reembed(args) -> None:
    """Re-embed stale content with updated models."""
    logger = logging.getLogger(__name__)

    if not args.if_stale:
        logger.error("--if-stale duration is required for re-embedding")
        return

    try:
        stale_threshold = parse_duration(args.if_stale)
        cutoff_date = datetime.now() - stale_threshold

        logger.info(
            f"Re-embedding content older than {args.if_stale} "
            f"(before {cutoff_date.isoformat()})"
        )

        memory = Memory(db_path=args.db_path)
        
        # Find stale embeddings using session
        from serena.database.session import get_db_session
        with get_db_session() as session:
            from serena.core.models import Archive
            
            # Find archives with stale embeddings
            stale_archives = session.query(Archive).filter(
                (Archive.last_embedded_at < cutoff_date) | 
                (Archive.last_embedded_at.is_(None))
            ).order_by(Archive.last_embedded_at.asc()).all()
            
            stale_tasks = [
                {
                    "task_id": archive.task_id,
                    "title": archive.title,
                    "filepath": archive.filepath,
                    "last_embedded_at": archive.last_embedded_at
                }
                for archive in stale_archives
            ]

        if not stale_tasks:
            logger.info("No stale embeddings found")
            return

        logger.info(f"Found {len(stale_tasks)} tasks with stale embeddings")

        if args.dry_run:
            logger.info("DRY RUN - Would re-embed the following tasks:")
            for task in stale_tasks:
                last_embedded = task["last_embedded_at"] or "Never"
                print(f"  {task['task_id']}: {task['title']} (last: {last_embedded})")
            return

        # Re-embed each task
        success_count = 0
        for i, task in enumerate(stale_tasks, 1):
            try:
                # Read file content
                with open(task["filepath"], "r", encoding="utf-8") as f:
                    content = f.read()

                # Re-index with new embeddings
                if memory.upsert(task["task_id"], content, filepath=task["filepath"]):
                    success_count += 1
                    logger.debug(f"Re-embedded task {task['task_id']}")
                else:
                    logger.warning(f"Failed to re-embed task {task['task_id']}")

                # Show progress
                if i % 10 == 0 or i == len(stale_tasks):
                    progress = (i / len(stale_tasks)) * 100
                    print(f"Progress: {i}/{len(stale_tasks)} ({progress:.1f}%)")

            except Exception as e:
                logger.error(f"Failed to process task {task['task_id']}: {e}")

        logger.info(
            f"Re-embedding completed: {success_count}/{len(stale_tasks)} successful"
        )

    except Exception as e:
        logger.error(f"Re-embedding failed: {e}")


def cmd_health(args) -> None:
    """Show detailed health information."""
    logger = logging.getLogger(__name__)

    memory = Memory(db_path=args.db_path)
    health = memory.health()

    print("Memory Bridge Health Report")
    print("=" * 50)
    print(f"Database path: {memory.db_path}")
    print(f"Database size: {health.database_size / (1024*1024):.1f} MB")
    print(f"Archive count: {health.archive_count}")
    print(f"Embedding count: {health.embedding_count}")

    if health.embedding_versions:
        print(f"Embedding versions: {health.embedding_versions}")

    if health.wal_checkpoint_age is not None:
        print(f"WAL checkpoint age: {health.wal_checkpoint_age} seconds")
        if health.wal_checkpoint_age > 3600:  # 1 hour
            print("  WARNING: WAL file is getting old, consider checkpoint")

    if args.detailed:
        try:
            from serena.database.session import get_db_session
            with get_db_session() as session:
                from serena.core.models import Archive
                from sqlalchemy import func

                # Task kind distribution
                kind_stats = session.query(
                    Archive.kind, 
                    func.count(Archive.task_id).label('count')
                ).group_by(Archive.kind).order_by(func.count(Archive.task_id).desc()).all()

                print("\nTask distribution by kind:")
                for kind, count in kind_stats:
                    print(f"  {kind}: {count}")

                # Status distribution
                status_stats = session.query(
                    Archive.status,
                    func.count(Archive.task_id).label('count')
                ).filter(Archive.status.isnot(None)).group_by(Archive.status).order_by(func.count(Archive.task_id).desc()).all()

                print("\nTask distribution by status:")
                for status, count in status_stats:
                    print(f"  {status}: {count}")

                # Recent activity (last 7 days)
                from datetime import datetime, timedelta
                seven_days_ago = datetime.now() - timedelta(days=7)
                recent_count = session.query(Archive).filter(Archive.created_at > seven_days_ago).count()
                print(f"\nRecent activity (last 7 days): {recent_count} new archives")

                # Embedding age distribution
                one_day_ago = datetime.now() - timedelta(days=1)
                one_week_ago = datetime.now() - timedelta(days=7)
                one_month_ago = datetime.now() - timedelta(days=30)
                six_months_ago = datetime.now() - timedelta(days=180)
                
                # Calculate age groups
                age_groups = [
                    ("Last 24h", session.query(Archive).filter(Archive.last_embedded_at > one_day_ago).count()),
                    ("Last week", session.query(Archive).filter(
                        (Archive.last_embedded_at <= one_day_ago) & 
                        (Archive.last_embedded_at > one_week_ago)
                    ).count()),
                    ("Last month", session.query(Archive).filter(
                        (Archive.last_embedded_at <= one_week_ago) & 
                        (Archive.last_embedded_at > one_month_ago)
                    ).count()),
                    ("Last 6 months", session.query(Archive).filter(
                        (Archive.last_embedded_at <= one_month_ago) & 
                        (Archive.last_embedded_at > six_months_ago)
                    ).count()),
                    ("Older than 6 months", session.query(Archive).filter(
                        Archive.last_embedded_at <= six_months_ago
                    ).count())
                ]

                print("\nEmbedding age distribution:")
                for age_group, count in age_groups:
                    if count > 0:
                        print(f"  {age_group}: {count}")

        except Exception as e:
            logger.error(f"Failed to get detailed health info: {e}")


def main():
    """Main maintenance script entry point."""
    parser = argparse.ArgumentParser(
        description="Memory Bridge database maintenance utilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--db-path",
        help="Path to SQLite database (default: from SERENA_MEMORY_DB env var)",
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    # Maintenance operations
    parser.add_argument(
        "--checkpoint",
        action="store_true",
        help="Perform WAL checkpoint and optimization",
    )

    parser.add_argument(
        "--vacuum", action="store_true", help="Perform database vacuum to reclaim space"
    )

    parser.add_argument(
        "--reembed",
        action="store_true",
        help="Re-embed stale content (requires --if-stale)",
    )

    parser.add_argument(
        "--if-stale",
        help='Duration threshold for re-embedding (e.g., "180d", "7d", "24h")',
    )

    parser.add_argument(
        "--health", action="store_true", help="Show database health information"
    )

    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed health information (with --health)",
    )

    args = parser.parse_args()

    # Check that at least one operation is specified
    operations = [args.checkpoint, args.vacuum, args.reembed, args.health]
    if not any(operations):
        parser.error("At least one operation must be specified")

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Set database path if provided
        if args.db_path:
            os.environ["SERENA_MEMORY_DB"] = args.db_path

        db_path = get_database_path()

        if not Path(db_path).exists():
            logger.error(f"Database not found: {db_path}")
            logger.error("Run migration script first to initialize the database")
            sys.exit(1)

        args.db_path = db_path

        # Execute requested operations
        if args.checkpoint:
            cmd_checkpoint(args)

        if args.vacuum:
            cmd_vacuum(args)

        if args.reembed:
            cmd_reembed(args)

        if args.health:
            cmd_health(args)

        logger.info("Maintenance operations completed successfully")

    except KeyboardInterrupt:
        print("\nMaintenance cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Maintenance failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# Lightweight service wrapper for API server
# ---------------------------------------------------------------------------


import threading


class MaintenanceService:  # noqa: D101 – simple wrapper
    """Background thread that periodically runs maintenance operations.

    This minimal implementation satisfies the server import without adding
    extra dependencies or complexity.
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.MaintenanceService")
        self.interval = parse_duration(settings.maintenance.intervals.health_check).total_seconds()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._last_status: dict = {}

        # Load last run timestamps from DB (persistent across restarts)
        self._last_checkpoint = self._load_meta_timestamp("last_checkpoint")
        self._last_vacuum = self._load_meta_timestamp("last_vacuum")

        if settings.maintenance.notifications.enable_file_logging:
            log_file = settings.maintenance.notifications.log_file
            handler = logging.FileHandler(log_file)
            handler.setFormatter(
                logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            )
            logging.getLogger().addHandler(handler)

        # Log initialization with both logging and print for visibility
        init_msg = "🔧 MaintenanceService initialized"
        print(init_msg)
        self.logger.info(init_msg)
        
        config_msgs = [
            f"   - Health check interval: {self.interval}s",
            f"   - Checkpoint interval: {settings.maintenance.intervals.checkpoint}",
            f"   - Vacuum interval: {settings.maintenance.intervals.vacuum}",
            f"   - Last checkpoint: {self._format_timestamp(self._last_checkpoint)}",
            f"   - Last vacuum: {self._format_timestamp(self._last_vacuum)}"
        ]
        
        for msg in config_msgs:
            print(msg)
            self.logger.info(msg)

    def _format_timestamp(self, timestamp: float) -> str:
        """Format a Unix timestamp for logging."""
        if timestamp == 0.0:
            return "Never"
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

    # ------------------------------------------------------------------
    # Public API expected by CLI Handler
    # ------------------------------------------------------------------

    def start_background_service(self):
        if self._thread and self._thread.is_alive():
            self.logger.debug("Background service already running")
            return

        start_msg = "🚀 Starting maintenance background service"
        print(start_msg)
        self.logger.info(start_msg)
        
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        
        success_msg = "✅ Maintenance background service started successfully"
        print(success_msg)
        self.logger.info(success_msg)

    def stop(self):
        self.logger.info("🛑 Stopping maintenance background service")
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
            if self._thread.is_alive():
                self.logger.warning("⚠️  Background service thread did not stop within timeout")
            else:
                self.logger.info("✅ Maintenance background service stopped successfully")

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_meta_timestamp(key: str) -> float:
        """Return stored UNIX timestamp for *key* or 0 if none."""
        from serena.database.session import get_db_session
        try:
            with get_db_session() as session:
                ts = session.execute(
                    text("CREATE TABLE IF NOT EXISTS maintenance_meta (key TEXT PRIMARY KEY, value TEXT);")
                )  # noqa: F841 – ensure table exists
                value = session.execute(
                    text("SELECT value FROM maintenance_meta WHERE key = :k"),
                    {"k": key},
                ).scalar()
                return float(value) if value else 0.0
        except Exception:
            return 0.0

    @staticmethod
    def _store_meta_timestamp(key: str, ts: float) -> None:
        from serena.database.session import get_db_session
        with get_db_session() as session:
            session.execute(
                text("CREATE TABLE IF NOT EXISTS maintenance_meta (key TEXT PRIMARY KEY, value TEXT);")
            )
            session.execute(
                text(
                    "INSERT INTO maintenance_meta(key, value) VALUES (:k, :v) "
                    "ON CONFLICT(key) DO UPDATE SET value = excluded.value"
                ),
                {"k": key, "v": str(ts)},
            )
            session.commit()

    # ------------------------------------------------------------------

    def run_operation(self, operation: str):
        if not getattr(settings.maintenance.enabled, operation, False):
            self.logger.debug(f"⏭️ Skipping disabled maintenance operation: {operation}")
            return

        start_time = time.time()
        op_start_msg = f"🔄 Starting maintenance operation: {operation}"
        print(op_start_msg)
        self.logger.info(op_start_msg)

        try:
            if operation == "checkpoint":
                self.logger.debug("   - Performing WAL checkpoint...")
                checkpoint_database()
                now = time.time()
                self._last_checkpoint = now
                self._store_meta_timestamp("last_checkpoint", now)
                elapsed = now - start_time
                checkpoint_msg = f"✅ Checkpoint completed successfully in {elapsed:.2f}s"
                print(checkpoint_msg)
                self.logger.info(checkpoint_msg)
                
            elif operation == "vacuum":
                self.logger.debug("   - Performing database vacuum...")
                # Create a mock args object for cmd_vacuum
                class MockArgs:
                    db_path = get_database_path()

                cmd_vacuum(MockArgs())
                now = time.time()
                self._last_vacuum = now
                self._store_meta_timestamp("last_vacuum", now)
                elapsed = now - start_time
                vacuum_msg = f"✅ Vacuum completed successfully in {elapsed:.2f}s"
                print(vacuum_msg)
                self.logger.info(vacuum_msg)
                
            elif operation == "health_check":
                self.logger.debug("   - Performing health check...")
                health = Memory().health()
                self._last_status = health.__dict__
                elapsed = time.time() - start_time
                self.logger.debug(f"📊 Health check completed: {health.archive_count} archives, "
                                f"{health.embedding_count} embeddings, "
                                f"{health.database_size / (1024*1024):.1f}MB ({elapsed:.2f}s)")
            else:
                raise ValueError(f"Unknown maintenance operation: {operation}")
                
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(f"❌ Maintenance operation '{operation}' failed after {elapsed:.2f}s: {e}")
            raise

    # Alias used earlier in CLI
    def run_specific_operation(self, operation: str):
        self.run_operation(operation)

    def get_status(self) -> dict:
        return {
            "last_health": self._last_status,
            "next_run_seconds": max(0, self.interval - int(self._elapsed_since_last())),
            "last_checkpoint": self._last_checkpoint,
            "last_vacuum": self._last_vacuum,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_loop(self):
        last_checkpoint = self._last_checkpoint or time.time()
        last_vacuum = self._last_vacuum or time.time()
        cycle_count = 0
        
        loop_msg = "🔄 Maintenance loop started"
        print(loop_msg)
        self.logger.info(loop_msg)

        while not self._stop.is_set():
            now = time.time()
            cycle_count += 1
            
            # Log cycle info every 10 cycles (for health check every ~5min, log every ~50min)
            if cycle_count % 10 == 1:
                checkpoint_interval = parse_duration(settings.maintenance.intervals.checkpoint).total_seconds()
                vacuum_interval = parse_duration(settings.maintenance.intervals.vacuum).total_seconds()
                
                next_checkpoint = max(0, checkpoint_interval - (now - last_checkpoint))
                next_vacuum = max(0, vacuum_interval - (now - last_vacuum))
                
                self.logger.debug(f"🕐 Maintenance cycle #{cycle_count}")
                self.logger.debug(f"   - Next checkpoint in: {next_checkpoint/60:.1f} minutes")
                self.logger.debug(f"   - Next vacuum in: {next_vacuum/3600:.1f} hours")
            
            try:
                # Health check always runs at the main interval
                self.run_operation("health_check")

                # Checkpoint interval
                checkpoint_interval = parse_duration(
                    settings.maintenance.intervals.checkpoint
                ).total_seconds()
                if now - last_checkpoint > checkpoint_interval:
                    self.run_operation("checkpoint")
                    last_checkpoint = now

                # Vacuum interval
                vacuum_interval = parse_duration(
                    settings.maintenance.intervals.vacuum
                ).total_seconds()
                if now - last_vacuum > vacuum_interval:
                    self.run_operation("vacuum")
                    last_vacuum = now

            except Exception:  # pragma: no cover
                self.logger.warning("Maintenance operation failed", exc_info=True)
                
            self._stop.wait(self.interval)
            
        self.logger.info("🏁 Maintenance loop ended")

    def _elapsed_since_last(self) -> float:
        import time

        return time.time() % self.interval
