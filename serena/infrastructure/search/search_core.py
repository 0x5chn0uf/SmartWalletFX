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
        Perform semantic search with optimized batch vector operations.

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

        # Get candidate embeddings (optimized single query)
        candidates = self._get_candidates_optimized(
            kind_filter, status_filter, first_chunk_only=True
        )

        if not candidates:
            return []

        # Extract vectors for batch processing
        vectors = [candidate["vector"] for candidate in candidates]

        def _score_candidates_batch(
            emb: List[float], search_text: str
        ) -> List[tuple[float, float, Dict[str, Any]]]:
            """Batch score all candidates with vectorized operations."""
            
            # Vectorized similarity calculation - much faster than individual calculations
            similarities = batch_cosine_similarity(emb, vectors)
            
            # Filter and score in batch
            scored_tuples = []
            for i, (candidate, sim) in enumerate(zip(candidates, similarities)):
                if sim < min_score:
                    continue
                
                # Calculate hybrid score (BM25 + recency factors)
                hybrid_score = self._calculate_hybrid_score_fast(sim, candidate, search_text)
                scored_tuples.append((hybrid_score, sim, candidate))
            
            return scored_tuples

        # Score all candidates in batch
        scored = _score_candidates_batch(query_embedding, query)

        # If no results, try token-based fallback
        if not scored and " " in query:
            tokens = [t for t in query.split() if len(t) >= 3]
            for tok in tokens[:3]:  # Limit to first 3 tokens for performance
                tok_emb = generate_embedding(tok)
                scored.extend(_score_candidates_batch(tok_emb, tok))

        if not scored:
            return []

        # Deduplicate by task_id, keeping highest score
        best_map: Dict[str, tuple[float, float, Dict[str, Any]]] = {}
        for score, sim, cand in scored:
            tid = cand["task_id"]
            if tid not in best_map or score > best_map[tid][0]:
                best_map[tid] = (score, sim, cand)

        # Sort and limit results
        top = sorted(best_map.values(), key=lambda x: x[0], reverse=True)[:k]

        # Build final results
        results: List[SearchResult] = []
        for score, similarity, candidate in top:
            excerpt = self._generate_excerpt_fast(candidate, query)
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

        # Cleanup memory - explicit cleanup of large arrays
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

    def _get_candidates_optimized(
        self,
        kind_filter: Optional[List[TaskKind]] = None,
        status_filter: Optional[List[TaskStatus]] = None,
        first_chunk_only: bool = False,
        limit: int = 1000,  # Reasonable limit to prevent memory issues
    ) -> List[Dict[str, Any]]:
        """Optimized candidate retrieval using single SQL query with batch processing."""
        import numpy as np
        from sqlalchemy import text
        
        # Build parameterized WHERE clause
        where_conditions = []
        params = {}
        
        if kind_filter:
            # Use parameterized query to prevent SQL injection
            kind_values = [
                kind.value if hasattr(kind, "value") else str(kind)
                for kind in kind_filter
            ]
            where_conditions.append("a.kind = ANY(:kind_values)")
            params["kind_values"] = kind_values
        
        if status_filter:
            status_values = [
                status.value if hasattr(status, "value") else str(status)
                for status in status_filter
            ]
            where_conditions.append("a.status = ANY(:status_values)")
            params["status_values"] = status_values
        
        if first_chunk_only:
            where_conditions.append("e.chunk_id = 0")
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Optimized query: fetch only necessary data, use indexes effectively
        query = f"""
            SELECT 
                a.task_id, a.title, a.kind, a.status, a.completed_at, a.filepath,
                e.vector, e.chunk_id, e.position
            FROM archives a
            INNER JOIN embeddings e ON a.task_id = e.task_id
            {where_clause}
            ORDER BY 
                a.completed_at DESC NULLS LAST, 
                e.chunk_id ASC, 
                e.position ASC
            LIMIT :limit
        """
        
        params["limit"] = limit
        
        candidates = []
        seen_task_ids = set()
        
        try:
            with get_session(self.db_path) as session:
                result = session.execute(text(query), params)
                
                # Batch process results for better memory efficiency
                batch_size = 100
                current_batch = []
                
                for row in result:
                    # Skip duplicates if we've seen this task_id (for first_chunk_only)
                    if first_chunk_only and row[0] in seen_task_ids:
                        continue
                    
                    if first_chunk_only:
                        seen_task_ids.add(row[0])
                    
                    current_batch.append(row)
                    
                    # Process batch when full
                    if len(current_batch) >= batch_size:
                        candidates.extend(self._process_candidate_batch(current_batch))
                        current_batch = []
                
                # Process remaining items
                if current_batch:
                    candidates.extend(self._process_candidate_batch(current_batch))
                
        except Exception as exc:
            logger.error(f"Optimized candidate query failed: {exc}")
            # Fallback to original method
            return self._get_candidates(kind_filter, status_filter, first_chunk_only)
        
        logger.debug(f"Retrieved {len(candidates)} candidates using optimized query")
        return candidates
    
    def _process_candidate_batch(self, batch_rows: List[tuple]) -> List[Dict[str, Any]]:
        """Process a batch of candidate rows efficiently."""
        import numpy as np
        
        candidates = []
        
        for row in batch_rows:
            try:
                # Convert vector bytes to numpy array, then to list for consistency
                vec_array = np.frombuffer(row[6], dtype=np.float32)
                vector = vec_array.tolist()
                
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
                
                # Explicit cleanup of numpy array
                del vec_array
                
            except Exception as exc:
                logger.warning(f"Failed to process candidate row: {exc}")
                continue
        
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

    def _calculate_hybrid_score_fast(
        self, similarity: float, candidate: Dict[str, Any], query: str
    ) -> float:
        """Fast hybrid score calculation with reduced BM25 overhead."""
        # Start with semantic similarity (70% weight)
        score = 0.7 * similarity
        
        # Quick text relevance check instead of full BM25 (for performance)
        title = candidate.get("title", "").lower()
        query_lower = query.lower()
        
        # Simple term matching boost (replaces expensive BM25 calculation)
        query_terms = query_lower.split()
        title_match_score = sum(1 for term in query_terms if term in title) / len(query_terms) if query_terms else 0
        score += 0.2 * title_match_score
        
        # Quick recency boost calculation
        if candidate["completed_at"]:
            try:
                # Use string parsing for speed (avoid datetime parsing in tight loop)
                # Assuming ISO format: YYYY-MM-DD...
                date_str = candidate["completed_at"][:10]  # Extract YYYY-MM-DD
                year, month, day = map(int, date_str.split('-'))
                
                # Simple days calculation (approximate)
                from datetime import datetime
                completed_date = datetime(year, month, day)
                days_ago = (datetime.now() - completed_date).days
                
                # Logarithmic recency boost (more recent = higher score)
                recency_boost = max(-0.1, -0.01 * math.log1p(days_ago / 30))  # Monthly decay
                score += recency_boost
            except Exception:
                pass  # Skip recency boost on error
        
        # Apply kind-based weights (cached for performance)
        kind_weights = {
            "archive": 1.0,
            "reflection": 1.1,
            "doc": 0.9,
            "rule": 0.8,
        }
        
        kind = candidate.get("kind", "archive")
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

    def _generate_excerpt_fast(self, candidate: Dict[str, Any], query: str) -> str:
        """Fast excerpt generation with caching and simplified processing."""
        try:
            # Use title as fallback first (most common case)
            fallback_excerpt = candidate.get("title", "")[:256]
            
            # Quick file existence check
            filepath = candidate.get("filepath", "")
            if not filepath or not os.path.exists(filepath):
                return fallback_excerpt
            
            # Check file size - skip large files for performance
            try:
                file_size = os.path.getsize(filepath)
                if file_size > 100 * 1024:  # Skip files larger than 100KB
                    return fallback_excerpt
            except OSError:
                return fallback_excerpt
            
            # Read file with size limit
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    # Read only first 5KB for excerpt generation
                    content = f.read(5120)
            except Exception:
                return fallback_excerpt
            
            if not content.strip():
                return fallback_excerpt
            
            # Fast excerpt extraction
            query_terms = query.lower().split()
            content_lower = content.lower()
            
            # Find best match position using simple search
            best_position = 0
            best_score = 0
            
            # Search in 200-char windows
            window_size = 200
            step_size = 100
            
            for i in range(0, min(len(content), 2000), step_size):  # Search first 2KB only
                window = content_lower[i:i + window_size]
                # Count query term matches in this window
                score = sum(1 for term in query_terms if term in window)
                
                if score > best_score:
                    best_score = score
                    best_position = i
            
            # Extract excerpt around best position
            start = max(0, best_position - 25)
            end = min(len(content), best_position + 225)
            excerpt = content[start:end].strip()
            
            # Clean up whitespace
            excerpt = " ".join(excerpt.split())
            
            # Truncate if needed
            if len(excerpt) > 256:
                excerpt = excerpt[:253] + "..."
            
            return excerpt or fallback_excerpt
            
        except Exception as exc:
            logger.debug(f"Fast excerpt generation failed: {exc}")
            return candidate.get("title", "")[:256]
