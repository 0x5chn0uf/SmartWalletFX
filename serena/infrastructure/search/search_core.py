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
                        completed_at=datetime.fromisoformat(candidate["completed_at"])
                        if candidate["completed_at"]
                        else None,
                        filepath=candidate["filepath"],
                    )
                )

            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def _fallback_keyword_search(
        self,
        query: str,
        k: int,
        kind_filter: Optional[List[TaskKind]] = None,
        status_filter: Optional[List[TaskStatus]] = None,
    ) -> List[SearchResult]:
        """Fallback search when embeddings are unavailable."""
        
        where_conditions = []
        params: List[Any] = []

        if kind_filter:
            placeholders = ",".join("?" * len(kind_filter))
            where_conditions.append(f"a.kind IN ({placeholders})")
            params.extend(
                [
                    knd.value if hasattr(knd, "value") else str(knd)
                    for knd in kind_filter
                ]
            )

        if status_filter:
            placeholders = ",".join("?" * len(status_filter))
            where_conditions.append(f"a.status IN ({placeholders})")
            params.extend(
                [
                    sts.value if hasattr(sts, "value") else str(sts)
                    for sts in status_filter
                ]
            )

        results: List[SearchResult] = []
        
        # Use session context manager correctly
        with get_connection(self.db_path) as session:
            from sqlalchemy import text
            import sqlite3
            
            # Try FTS table first
            use_fts = False
            try:
                session.execute(text("SELECT 1 FROM archives_fts LIMIT 1"))
                use_fts = True
            except Exception:
                use_fts = False

            if use_fts:
                where_clause = (
                    "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
                )
                sql = f"""
                    SELECT a.task_id, a.title, a.kind, a.status, a.completed_at, a.filepath,
                           bm25(archives_fts) AS rank
                    FROM archives_fts
                    JOIN archives a USING(task_id)
                    WHERE archives_fts MATCH ? {where_clause}
                    ORDER BY rank LIMIT ?
                """
                params = [query] + params + [k]
                result = session.execute(text(sql), params)
            else:
                # Simple LIKE on title as last resort
                where_conditions.append("a.title LIKE ?")
                params.append(f"%{query}%")
                where_clause = "WHERE " + " AND ".join(where_conditions)
                sql = f"""
                    SELECT a.task_id, a.title, a.kind, a.status, a.completed_at, a.filepath,
                           0 as rank
                    FROM archives a {where_clause}
                    ORDER BY a.completed_at DESC LIMIT ?
                """
                params.append(k)
                result = session.execute(text(sql), params)

            for row in result:
                results.append(
                    SearchResult(
                        task_id=row[0],  # task_id
                        title=row[1],    # title  
                        score=float(row[6]),  # rank
                        excerpt="",
                        kind=TaskKind(row[2]),  # kind
                        status=TaskStatus(row[3]) if row[3] else None,  # status
                        completed_at=datetime.fromisoformat(row[4])  # completed_at
                        if row[4]
                        else None,
                        filepath=row[5],  # filepath
                    )
                )

        # Generate excerpts lazily
        for res in results:
            res.excerpt = self._generate_excerpt(
                {"filepath": res.filepath, "title": res.title}, query
            )

        return results

    def _get_candidates(
        self,
        kind_filter: Optional[List[TaskKind]] = None,
        status_filter: Optional[List[TaskStatus]] = None,
        first_chunk_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get candidate records with embeddings from database."""
        
        # Build WHERE clause for filters
        where_conditions = []
        params = []

        if kind_filter:
            kind_placeholders = ",".join("?" * len(kind_filter))
            where_conditions.append(f"a.kind IN ({kind_placeholders})")
            params.extend(
                [
                    kind.value if hasattr(kind, "value") else str(kind)
                    for kind in kind_filter
                ]
            )

        if status_filter:
            status_placeholders = ",".join("?" * len(status_filter))
            where_conditions.append(f"a.status IN ({status_placeholders})")
            params.extend(
                [
                    status.value if hasattr(status, "value") else str(status)
                    for status in status_filter
                ]
            )

        if first_chunk_only:
            where_conditions.append("e.chunk_id = 0")

        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)

        query = f"""
            SELECT 
                a.task_id, a.title, a.kind, a.status, a.completed_at, a.filepath,
                e.vector, e.chunk_id, e.position
            FROM archives a
            JOIN embeddings e ON a.task_id = e.task_id
            {where_clause}
            ORDER BY a.completed_at DESC NULLS LAST, e.chunk_id ASC
        """

        candidates = []
        seen_task_ids = set()
        
        # Use session context manager correctly
        with get_connection(self.db_path) as session:
            from sqlalchemy import text
            result = session.execute(text(query), params)
            
            for row in result:
                # Skip if we've already seen this task_id (deduplication)
                if row[0] in seen_task_ids:  # task_id is first column
                    continue

                seen_task_ids.add(row[0])

                # Convert vector bytes back to list
                import numpy as np
                vector = np.frombuffer(row[6], dtype=np.float32).tolist()  # vector is 7th column

                candidate = {
                    "task_id": row[0],
                    "title": row[1],
                    "kind": row[2],
                    "status": row[3],
                    "completed_at": row[4],
                    "filepath": row[5],
                    "vector": vector,
                    "chunk_id": row[7],
                    "position": row[8],
                }
                candidates.append(candidate)

        return candidates

    def _calculate_hybrid_score(
        self, similarity: float, candidate: Dict[str, Any], query: str
    ) -> float:
        """Calculate hybrid score combining similarity, BM25, and recency."""
        # Base score from semantic similarity (70% weight)
        score = 0.7 * similarity

        # Try to add BM25 score if FTS is available (30% weight)
        try:
            bm25_score = self._calculate_bm25_score(candidate["task_id"], query)
            score += 0.3 * bm25_score
        except Exception:
            # FTS not available, use pure semantic similarity
            pass

        # Apply recency boost
        if candidate["completed_at"]:
            try:
                completed_date = datetime.fromisoformat(candidate["completed_at"])
                days_ago = (datetime.now() - completed_date).days
                recency_boost = math.log1p(days_ago) * -0.05
                score += recency_boost
            except Exception:
                pass

        # Apply kind-based weights
        kind_weights = {
            TaskKind.ARCHIVE: 1.0,
            TaskKind.REFLECTION: 1.1,  # Slight boost for reflections
            TaskKind.DOC: 0.9,
            TaskKind.RULE: 0.8,
        }

        kind = TaskKind(candidate["kind"])
        score *= kind_weights.get(kind, 1.0)

        return max(0.0, min(1.0, score))  # Clamp to [0, 1]

    def _calculate_bm25_score(self, task_id: str, query: str) -> float:
        """Calculate BM25 score using FTS5 if available."""
        try:
            conn = get_connection(self.db_path)

            # Use FTS5 to get BM25 score
            cursor = conn.execute(
                """
                SELECT bm25(archives_fts) as score
                FROM archives_fts
                WHERE archives_fts MATCH ?
                AND task_id = ?
            """,
                (query, task_id),
            )

            row = cursor.fetchone()
            conn.close()

            if row and row["score"] is not None:
                # FTS5 BM25 scores are negative, normalize to 0-1
                raw_score = abs(row["score"])
                return min(1.0, raw_score / 10.0)  # Rough normalization

        except Exception:
            pass

        return 0.0

    def _generate_excerpt(self, candidate: Dict[str, Any], query: str) -> str:
        """Generate a relevant excerpt from the content."""
        try:
            # Try to read file content
            with open(candidate["filepath"], "r", encoding="utf-8") as f:
                content = f.read()

            # Find most relevant section containing query terms
            query_terms = query.lower().split()
            content_lower = content.lower()

            best_position = 0
            best_score = 0

            # Look for sections with most query terms
            for i in range(0, len(content), 100):
                section = content_lower[i : i + 300]
                score = sum(1 for term in query_terms if term in section)
                if score > best_score:
                    best_score = score
                    best_position = i

            # Extract excerpt around best position
            start = max(0, best_position - 50)
            end = min(len(content), best_position + 200)
            excerpt = content[start:end].strip()

            # Clean up excerpt
            excerpt = " ".join(excerpt.split())  # Normalize whitespace

            if len(excerpt) > 256:
                excerpt = excerpt[:253] + "..."

            return excerpt

        except Exception:
            # Fallback to title if file reading fails
            return candidate.get("title", "")[:256]