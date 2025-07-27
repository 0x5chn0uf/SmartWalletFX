"""Database connection and schema management for Serena memory bridge."""

from __future__ import annotations

import logging
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from serena import config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def get_database_path() -> str:
    """Return the configured SQLite database path."""
    return config.memory_db_path()


def init_database(db_path: Optional[str] = None) -> str:
    """Create tables / indexes if the database file does not yet exist."""
    if db_path is None:
        db_path = get_database_path()

    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")

    migrate_for_code_support(conn)

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS archives (
            task_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            filepath TEXT NOT NULL UNIQUE,
            sha256 TEXT NOT NULL UNIQUE,
            kind   TEXT NOT NULL CHECK (kind IN ('archive','reflection','doc','rule','code')),
            status TEXT,
            completed_at TIMESTAMP,
            embedding_id INTEGER,
            summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            embedding_version INTEGER DEFAULT 1,
            last_embedded_at TIMESTAMP
        )
    """,
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            chunk_id INTEGER NOT NULL DEFAULT 0,
            position INTEGER NOT NULL DEFAULT 0,
            vector BLOB NOT NULL,
            FOREIGN KEY (task_id) REFERENCES archives(task_id)
        )
    """,
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS maintenance_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation TEXT NOT NULL CHECK (operation IN ('checkpoint','vacuum','health_check')),
            started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            duration_seconds REAL,
            success BOOLEAN NOT NULL DEFAULT 0,
            details TEXT,
            error_message TEXT,
            db_size_before_mb REAL,
            db_size_after_mb REAL,
            space_saved_bytes INTEGER DEFAULT 0
        )
    """,
    )

    # indexes
    conn.execute("CREATE INDEX IF NOT EXISTS idx_archives_sha256 ON archives(sha256)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_archives_completed_at ON archives(completed_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_archives_kind ON archives(kind)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_task_id ON embeddings(task_id)")

    # FTS5 table (ignore errors if extension not present)
    try:
        conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS archives_fts USING fts5(
                task_id UNINDEXED,
                title,
                content,
                content_type=archives,
                tokenize='porter'
            )
        """,
        )
    except sqlite3.OperationalError:
        logger.info("FTS5 not available – keyword fallback only")

    conn.commit()
    conn.close()
    logger.info("Database ready at %s", db_path)
    return db_path


# ---------------------------------------------------------------------------
# Convenience wrappers
# ---------------------------------------------------------------------------

def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:  # noqa: D401
    if db_path is None:
        db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.row_factory = sqlite3.Row
    return conn


def checkpoint_database(db_path: Optional[str] = None) -> None:
    if db_path is None:
        db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    conn.execute("PRAGMA optimize")
    conn.close()


def vacuum_database(db_path: Optional[str] = None) -> None:
    if db_path is None:
        db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    conn.execute("VACUUM")
    conn.close()


# ---------------------------------------------------------------------------
# Migrations
# ---------------------------------------------------------------------------

def migrate_for_code_support(conn: sqlite3.Connection) -> None:
    """Ensure the 'code' kind is accepted in the archives.kind CHECK constraint."""
    try:
        current = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='archives'",
        ).fetchone()
        if not current or "'code'" in current[0]:
            return  # already fine

        logger.info("Migrating archives table to support 'code' kind…")
        conn.execute("CREATE TABLE archives_backup AS SELECT * FROM archives")
        conn.execute("DROP TABLE archives")
        # re-run create above via init_database logic (simpler):
        init_database(conn.execute("PRAGMA database_list").fetchone()[2])
        conn.execute("INSERT INTO archives SELECT * FROM archives_backup")
        conn.execute("DROP TABLE archives_backup")
        conn.commit()
    except Exception as exc:  # noqa: BLE001
        logger.error("Migration failed: %s", exc)
        conn.rollback()
        raise
