from __future__ import annotations

"""Memory service implementation using SQLAlchemy ORM."""

import logging
import os
import struct
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from serena import config
from serena.core.models import (
    Archive,
    Embedding,
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
    init_database,
)
from serena.database.session import get_db_session as get_session
from serena.infrastructure.embeddings import (
    EmbeddingGenerator,
    chunk_content,
    preprocess_content,
)
from serena.infrastructure.search import SearchEngine
from serena.infrastructure.search.search_utils import get_latest_tasks
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
            from serena.infrastructure.embeddings import get_default_generator
            self._embedding_generator = get_default_generator()
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
            with get_session(self.db_path) as session:
                archive = session.query(Archive).filter_by(task_id=task_id).first()
                if archive:
                    return {
                        "task_id": archive.task_id,
                        "title": archive.title,
                        "filepath": archive.filepath,
                        "kind": archive.kind,
                        "status": archive.status,
                        "completed_at": archive.completed_at,
                        "summary": archive.summary,
                        "content": None,  # Content not stored in Archive model
                    }
                return None
        except (OSError, IOError) as exc:
            logger.error("Database I/O error fetching task %s: %s", task_id, exc)
            return None
        except Exception as exc:
            logger.error("Unexpected error fetching task %s: %s", task_id, exc)
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
            with get_session(self.db_path) as session:
                # Upsert main archive row
                archive = session.query(Archive).filter_by(task_id=task_id).first()
                
                if archive:
                    # Update existing archive
                    archive.title = title or extract_title(markdown_text)
                    archive.filepath = filepath or f"archive-{task_id}.md"
                    archive.sha256 = compute_content_hash(markdown_text)
                    archive.kind = (kind or TaskKind.ARCHIVE).value
                    archive.status = status.value if status else None
                    archive.completed_at = completed_at
                    archive.summary = generate_summary(markdown_text)
                    archive.updated_at = datetime.now()
                else:
                    # Create new archive
                    archive = Archive(
                        task_id=task_id,
                        title=title or extract_title(markdown_text),
                        filepath=filepath or f"archive-{task_id}.md",
                        sha256=compute_content_hash(markdown_text),
                        kind=(kind or TaskKind.ARCHIVE).value,
                        status=status.value if status else None,
                        completed_at=completed_at,
                        summary=generate_summary(markdown_text),
                    )
                    session.add(archive)

                # Delete existing embeddings for this task
                session.query(Embedding).filter_by(task_id=task_id).delete()

                # Add new embeddings if available
                if chunks and self.embedding_generator.model is not None:
                    embeddings = self.embedding_generator.generate_embeddings_batch(
                        [chunk for chunk, _ in chunks]
                    )
                    for (chunk_text, chunk_pos), vector in zip(chunks, embeddings):
                        # Convert vector to bytes (simplified)
                        vector_bytes = bytearray()
                        for f in vector:
                            vector_bytes.extend(struct.pack("<f", f))
                        
                        embedding = Embedding(
                            task_id=task_id,
                            chunk_id=chunk_pos,
                            position=0,
                            vector=bytes(vector_bytes),
                        )
                        session.add(embedding)

                # Session commit happens automatically via context manager
                logger.debug("Upserted task %s", task_id)
                return True
        except (OSError, IOError) as exc:
            logger.error("Database I/O error during upsert for %s: %s", task_id, exc)
            return False
        except Exception as exc:
            logger.error("Unexpected error during upsert for %s: %s", task_id, exc)
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
        """Get database health information."""
        try:
            with get_session(self.db_path) as session:
                archive_count = session.query(Archive).count()
                embedding_count = session.query(Embedding).count()
                
                return HealthInfo(
                    archive_count=archive_count,
                    embedding_count=embedding_count,
                    last_migration=None,
                    wal_checkpoint_age=None,
                    database_size=os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0,
                    embedding_versions={},
                )
        except Exception as exc:
            logger.error("Health check failed: %s", exc)
            return HealthInfo(
                archive_count=0,
                embedding_count=0,
                last_migration=None,
                wal_checkpoint_age=None,
                database_size=0,
                embedding_versions={},
            )


# Helper to extract title from markdown (simple)


def extract_title(content: str) -> Optional[str]:
    for line in content.splitlines():
        if line.startswith("#"):
            return line.lstrip("# ").strip()
    return None
