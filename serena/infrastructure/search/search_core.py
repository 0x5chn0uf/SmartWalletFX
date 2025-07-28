"""Core search engine functionality."""

import logging
import math
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from serena.core.models import SearchResult, TaskKind, TaskStatus
from serena.database.session import get_db_session as get_session
from serena.infrastructure.embeddings import batch_cosine_similarity, generate_embedding
from serena.utils.error_handling import log_exceptions

from sqlalchemy import MetaData, Table, func, select, text  # type: ignore

logger = logging.getLogger(__name__)


class SearchEngine:
    """Handles semantic search with hybrid ranking."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    @log_exceptions(logger=logger, default_return=[])
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

        # Generate query embedding
        query_embedding = generate_embedding(query)

        # Embeddings must be available
        if not any(abs(x) > 1e-6 for x in query_embedding):
            raise RuntimeError(
                "Embeddings are disabled or unavailable; semantic search cannot proceed."
            )

        # Get candidate embeddings (only first chunk per task for speed)
        candidates = self._get_candidates(
            kind_filter, status_filter, first_chunk_only=True
        )

        if not candidates:
            return []

        vectors = [candidate["vector"] for candidate in candidates]

        def _score_candidates(
            emb: List[float], search_text: str
        ) -> List[tuple[float, float, Dict[str, Any]]]:
            """Return (score, similarity, candidate) tuples above threshold."""

            sims = batch_cosine_similarity(emb, vectors)
            tuples: List[tuple[float, float, Dict[str, Any]]] = []
            for cand, sim in zip(candidates, sims):
                if sim < min_score:
                    continue
                tuples.append((self._calculate_hybrid_score(sim, cand, search_text), sim, cand))
            
            # Cleanup similarity scores list
            del sims
            return tuples

        scored = _score_candidates(query_embedding, query)

        # If no result, broaden by individual tokens (length >=3)
        if not scored and " " in query:
            tokens = [t for t in query.split() if len(t) >= 3]
            for tok in tokens:
                tok_emb = generate_embedding(tok)
                scored.extend(_score_candidates(tok_emb, tok))

        if not scored:
            return []

        # Deduplicate by task_id keep highest score
        best_map: Dict[str, tuple[float, float, Dict[str, Any]]] = {}
        for score, sim, cand in scored:
            tid = cand["task_id"]
            if tid not in best_map or score > best_map[tid][0]:
                best_map[tid] = (score, sim, cand)

        top = sorted(best_map.values(), key=lambda x: x[0], reverse=True)[:k]

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

        # Cleanup vectors and candidates lists to free memory
        del vectors, candidates, scored, top
        
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
        with get_session(self.db_path) as session:
            from sqlalchemy import text
            result = session.execute(text(query), params)
            
            for row in result:
                # Skip if we've already seen this task_id (deduplication)
                if row[0] in seen_task_ids:  # task_id is first column
                    continue

                seen_task_ids.add(row[0])

                # Convert vector bytes back to list
                import numpy as np
                vec_array = np.frombuffer(row[6], dtype=np.float32)
                vector = vec_array.tolist()
                del vec_array  # Explicit cleanup of numpy array

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
        score = 0.7 * similarity

        bm25_score = self._calculate_bm25_score(candidate["task_id"], query)
        score += 0.3 * bm25_score

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
            with get_session(self.db_path) as session:
                # Reflect the FTS virtual table dynamically.  We avoid declaring it
                # in the SQLAlchemy models because it is created by the migration
                # script and has no primary key.
                metadata = MetaData()
                archives_fts = Table("archives_fts", metadata, autoload_with=session.get_bind())

                stmt = (
                    select(func.bm25(archives_fts).label("score"))
                    .where(archives_fts.c.task_id == task_id)
                    .where(text("archives_fts MATCH :query"))
                    .params(query=query)
                )

                result = session.execute(stmt).scalar_one_or_none()

                if result is None:
                    return 0.0  # No match found, return neutral score

                raw_score: float = abs(float(result))  # FTS5 returns negative values
                return min(1.0, raw_score / 10.0)  # Rough normalization
        except Exception:
            # FTS table doesn't exist or other error - return neutral score
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
            return candidate.get("title", "")[:256]