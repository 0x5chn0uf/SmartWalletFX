"""Core search engine functionality."""

import logging
import math
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from serena.core.models import SearchResult, TaskKind, TaskStatus
from serena.infrastructure.database import get_connection
from serena.infrastructure.embeddings import batch_cosine_similarity, generate_embedding

logger = logging.getLogger(__name__)


class SearchEngine:
    """Handles semantic search with hybrid ranking."""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize search engine.

        Args:
            db_path: Optional database path
        """
        self.db_path = db_path

    def search(
        self,
        query: str,
        k: int = 10,
        kind_filter: Optional[List[TaskKind]] = None,
        status_filter: Optional[List[TaskStatus]] = None,
        min_score: float = 0.1,
    ) -> List[SearchResult]:
        """
        Perform semantic search with optional filters.

        Args:
            query: Search query text
            k: Number of results to return
            kind_filter: Optional filter by task kinds
            status_filter: Optional filter by task statuses
            min_score: Minimum similarity score threshold

        Returns:
            List[SearchResult]: Ranked search results
        """
        if not query.strip():
            return []

        try:
            # Generate query embedding
            query_embedding = generate_embedding(query)

            # Detect if embeddings are effectively disabled (all-zero vector)
            if not any(abs(x) > 1e-6 for x in query_embedding):
                logger.info(
                    "Embeddings disabled or unavailable – falling back to FTS/LIKE search"
                )
                return self._fallback_keyword_search(
                    query, k, kind_filter, status_filter
                )

            # Get candidate embeddings (only first chunk per task for speed)
            candidates = self._get_candidates(
                kind_filter, status_filter, first_chunk_only=True
            )

            if not candidates:
                return []

            # Calculate semantic similarities
            vectors = [candidate["vector"] for candidate in candidates]
            similarities = batch_cosine_similarity(query_embedding, vectors)

            scored = []
            for candidate, similarity in zip(candidates, similarities):
                if similarity < min_score:
                    continue

                score = self._calculate_hybrid_score(similarity, candidate, query)
                scored.append((score, similarity, candidate))

            # Pick top-k by score without computing excerpts yet
            top = sorted(scored, key=lambda x: x[0], reverse=True)[:k]

            results: List[SearchResult] = []
            for score, similarity, candidate in top:
                excerpt = self._generate_excerpt(candidate, query)
                results.append(
                    SearchResult(
                        task_id=candidate["task_id"],
                        title=candidate["title"],
                        score=score,
                        excerpt=excerpt,
                        kind=TaskKind(candidate["kind"]),
                        status=TaskStatus(candidate["status"])
                        if candidate["status"]
                        else None,
                        filepath=candidate.get("filepath"),
                        completed_at=candidate.get("completed_at"),
                    )
                )

            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    # Internal helper methods will be moved here from the original file
    # This is just the core structure to start with