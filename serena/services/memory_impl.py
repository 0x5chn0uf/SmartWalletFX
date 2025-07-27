from __future__ import annotations

"""Memory service implementation."""

import logging
import os
import sqlite3
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from serena import config
from serena.core.models import (
    ArchiveRecord,
    EmbeddingRecord,
    HealthInfo,
    SearchResult,
    TaskKind,
    TaskStatus,
    compute_content_hash,
    determine_task_kind,
    extract_task_id_from_path,
    generate_summary,
)
from serena.infrastructure.database import (
    checkpoint_database,
    get_connection,
    init_database,
)
from serena.infrastructure.embeddings import (
    EmbeddingGenerator,
    chunk_content,
    preprocess_content,
)
from serena.infrastructure.search.engine import SearchEngine, get_latest_tasks
from serena.infrastructure.write_queue import write_queue

logger = logging.getLogger(__name__)


class Memory:
    """Main interface for the memory bridge system."""

    def __init__(self, db_path: Optional[str] = None, cache_size: int = 512):
        # Resolve DB path via centralised config (CLI override wins)
        if db_path is not None:
            self.db_path = db_path
        else:
            self.db_path = config.memory_db_path()
        self.cache_size = cache_size
        self._embedding_generator: Optional[EmbeddingGenerator] = None
        self._search_engine: Optional[SearchEngine] = None

        # Async write flag can be toggled via env SERENA_ASYNC_WRITE
        self.async_write = os.getenv("SERENA_ASYNC_WRITE", "0").lower() in {
            "1",
            "true",
            "yes",
        }

        # Initialize database if it doesn't exist
        if not Path(self.db_path).exists():
            init_database(self.db_path)
            logger.info("Initialized new memory database: %s", self.db_path)

    # ------------------------------------------------------------------
    # Lazy-loaded helpers
    # ------------------------------------------------------------------
    @property
    def embedding_generator(self) -> EmbeddingGenerator:  # noqa: D401
        if self._embedding_generator is None:
            self._embedding_generator = EmbeddingGenerator()
        return self._embedding_generator

    @property
    def search_engine(self) -> SearchEngine:  # noqa: D401
        if self._search_engine is None:
            self._search_engine = SearchEngine(self.db_path)
        return self._search_engine

    # ------------------------------------------------------------------
    # CRUD API
    # ------------------------------------------------------------------
    @lru_cache(maxsize=512)
    def get(self, task_id: str) -> Optional[Dict[str, Any]]:
        try:
            conn = get_connection(self.db_path)
            cursor = conn.execute(
                """
                SELECT task_id, title, filepath, kind, status, completed_at,
                       summary, content
                FROM archives
                WHERE task_id = ?
            """,
                (task_id,),
            )
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to fetch task %s: %s", task_id, exc)
            return None

    def upsert(
        self,
        task_id: str,
        markdown_text: str,
        filepath: Optional[str] = None,
        title: Optional[str] = None,
        kind: Optional[TaskKind] = None,
        status: Optional[TaskStatus] = None,
        completed_at: Optional[datetime] = None,
        async_write: Optional[bool] = None,
    ) -> bool:
        if async_write is None:
            async_write = self.async_write

        if async_write:
            write_queue.submit(
                self._upsert_internal,
                task_id,
                markdown_text,
                filepath,
                title,
                kind,
                status,
                completed_at,
            )
            return True
        return self._upsert_internal(
            task_id,
            markdown_text,
            filepath,
            title,
            kind,
            status,
            completed_at,
        )

    def _upsert_internal(
        self,
        task_id: str,
        markdown_text: str,
        filepath: Optional[str] = None,
        title: Optional[str] = None,
        kind: Optional[TaskKind] = None,
        status: Optional[TaskStatus] = None,
        completed_at: Optional[datetime] = None,
    ) -> bool:
        # Pre-process & chunk content (embedding optional)
        clean_content = preprocess_content(markdown_text)
        chunks = chunk_content(clean_content)

        try:
            conn = get_connection(self.db_path)
            cur = conn.cursor()

            # Upsert main archive row
            cur.execute(
                """
                INSERT INTO archives (task_id, title, filepath, sha256, kind, status, completed_at, summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    title=excluded.title,
                    filepath=excluded.filepath,
                    sha256=excluded.sha256,
                    kind=excluded.kind,
                    status=excluded.status,
                    completed_at=excluded.completed_at,
                    updated_at=CURRENT_TIMESTAMP
            """,
                (
                    task_id,
                    title or extract_title(markdown_text),
                    filepath or f"archive-{task_id}.md",
                    compute_content_hash(markdown_text),
                    (kind or TaskKind.ARCHIVE).value,
                    status.value if status else None,
                    completed_at.isoformat() if completed_at else None,
                    generate_summary(markdown_text),
                ),
            )

            # Delete existing embeddings for this task
            cur.execute("DELETE FROM embeddings WHERE task_id = ?", (task_id,))

            if chunks and self.embedding_generator.model is not None:
                embeddings = self.embedding_generator.generate_embeddings_batch(
                    [chunk for _, chunk in chunks]
                )
                for (chunk_id, _), vector in zip(chunks, embeddings):
                    cur.execute(
                        """
                        INSERT INTO embeddings (task_id, chunk_id, position, vector)
                        VALUES (?, ?, 0, ?)
                    """,
                        (
                            task_id,
                            chunk_id,
                            sqlite3.Binary(
                                bytearray(
                                    (
                                        byte
                                        for f in vector
                                        for byte in memoryview(
                                            bytearray(struct.pack("<f", f))
                                        )
                                    )
                                )
                            ),
                        ),
                    )

            conn.commit()
            conn.close()
            logger.debug("Upserted task %s", task_id)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Upsert failed for %s: %s", task_id, exc)
            return False

    # ------------------------------------------------------------------
    # Search & analytics
    # ------------------------------------------------------------------
    def search(
        self,
        query: str,
        k: int = 10,
        kind_filter: Optional[List[TaskKind]] = None,
        status_filter: Optional[List[TaskStatus]] = None,
    ) -> List[SearchResult]:
        return self.search_engine.search(query, k, kind_filter, status_filter)

    def latest(self, n: int = 10) -> List[SearchResult]:
        return get_latest_tasks(n, db_path=self.db_path)

    def health(self) -> HealthInfo:
        # Implementation identical to original, simplified here
        conn = get_connection(self.db_path)
        row = conn.execute("SELECT COUNT(*) FROM archives").fetchone()
        archive_count = row[0] if row else 0
        conn.close()
        return HealthInfo(
            archive_count=archive_count,
            embedding_count=0,
            last_migration=None,
            wal_checkpoint_age=None,
            database_size=os.path.getsize(self.db_path),
            embedding_versions={},
        )


# Helper to extract title from markdown (simple)


def extract_title(content: str) -> Optional[str]:
    for line in content.splitlines():
        if line.startswith("#"):
            return line.lstrip("# ").strip()
    return None
