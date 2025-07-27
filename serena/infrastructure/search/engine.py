"""Semantic search engine for Serena memory bridge."""

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

    # ------------------------------------------------------------------
    # Fallback search path when embeddings unavailable
    # ------------------------------------------------------------------
    def _fallback_keyword_search(
        self,
        query: str,
        k: int,
        kind_filter: Optional[List[TaskKind]] = None,
        status_filter: Optional[List[TaskStatus]] = None,
    ) -> List[SearchResult]:
        conn = get_connection(self.db_path)

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

        # Try FTS table first
        use_fts = False
        try:
            conn.execute("SELECT 1 FROM archives_fts LIMIT 1")
            use_fts = True
        except sqlite3.OperationalError:
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
            cursor = conn.execute(sql, params)
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
            cursor = conn.execute(sql, params)

        results: List[SearchResult] = []
        for row in cursor:
            results.append(
                SearchResult(
                    task_id=row["task_id"],
                    title=row["title"],
                    score=float(row["rank"]),
                    excerpt="",
                    kind=TaskKind(row["kind"]),
                    status=TaskStatus(row["status"]) if row["status"] else None,
                    completed_at=datetime.fromisoformat(row["completed_at"])
                    if row["completed_at"]
                    else None,
                    filepath=row["filepath"],
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
        """
        Get candidate records with embeddings from database.

        Args:
            kind_filter: Optional filter by task kinds
            status_filter: Optional filter by task statuses

        Returns:
            List[Dict]: Candidate records with metadata and embeddings
        """
        conn = get_connection(self.db_path)

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

        cursor = conn.execute(query, params)
        candidates = []
        seen_task_ids = set()

        for row in cursor:
            # Skip if we've already seen this task_id (deduplication)
            if row["task_id"] in seen_task_ids:
                continue

            seen_task_ids.add(row["task_id"])

            # Convert vector bytes back to list
            import numpy as np

            vector = np.frombuffer(row["vector"], dtype=np.float32).tolist()

            candidate = {
                "task_id": row["task_id"],
                "title": row["title"],
                "kind": row["kind"],
                "status": row["status"],
                "completed_at": row["completed_at"],
                "filepath": row["filepath"],
                "vector": vector,
                "chunk_id": row["chunk_id"],
                "position": row["position"],
            }
            candidates.append(candidate)

        conn.close()
        return candidates

    def _calculate_hybrid_score(
        self, similarity: float, candidate: Dict[str, Any], query: str
    ) -> float:
        """
        Calculate hybrid score combining similarity, BM25, and recency.

        Args:
            similarity: Cosine similarity score
            candidate: Candidate record metadata
            query: Original search query

        Returns:
            float: Hybrid score
        """
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
        """
        Calculate BM25 score using FTS5 if available.

        Args:
            task_id: Task ID to score
            query: Search query

        Returns:
            float: Normalized BM25 score (0-1)
        """
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
        """
        Generate a relevant excerpt from the content.

        Args:
            candidate: Candidate record
            query: Search query

        Returns:
            str: Generated excerpt (max 256 characters)
        """
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


class AdvancedSearchEngine(SearchEngine):
    """
    Enhanced search engine with advanced ranking algorithms and context-aware suggestions.
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)
        self.context_weights = {
            "task_complexity": 0.15,
            "task_urgency": 0.10,
            "user_history": 0.10,
            "domain_relevance": 0.20,
            "temporal_context": 0.05,
        }
        self.query_cache = {}
        self.suggestion_cache = {}

    def search_with_context(
        self,
        query: str,
        limit: int = 10,
        context: Optional[Dict[str, Any]] = None,
        enhance_query: bool = True,
    ) -> List[SearchResult]:
        """
        Enhanced search with context-aware ranking and query enhancement.

        Args:
            query: Search query
            limit: Maximum results to return
            context: Context information (task_id, complexity, urgency, etc.)
            enhance_query: Whether to enhance query with domain knowledge

        Returns:
            List of search results with enhanced ranking
        """
        # Cache key for enhanced queries
        cache_key = f"{query}_{hash(str(context))}" if context else query

        if cache_key in self.query_cache:
            return self.query_cache[cache_key][:limit]

        # Enhance query with domain knowledge if requested
        if enhance_query:
            query = self._enhance_query_with_domain_knowledge(query, context)

        # Get base candidates from parent class
        candidates = self._get_candidates()

        if not candidates:
            return []

        # Calculate enhanced scores with context awareness
        scored_candidates = []
        for candidate in candidates:
            similarity = self._get_embedding_similarity(query, candidate)
            enhanced_score = self._calculate_context_aware_score(
                similarity, candidate, query, context
            )

            scored_candidates.append(
                {
                    "candidate": candidate,
                    "score": enhanced_score,
                    "similarity": similarity,
                }
            )

        # Sort by enhanced score
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)

        # Generate results with enhanced excerpts
        results = []
        for item in scored_candidates[:limit]:
            candidate = item["candidate"]
            excerpt = self._generate_excerpt(candidate, query)

            result = SearchResult(
                task_id=candidate["task_id"],
                title=candidate["title"],
                score=item["score"],
                excerpt=excerpt,
                kind=TaskKind(candidate["kind"]),
                status=TaskStatus(candidate["status"]) if candidate["status"] else None,
                completed_at=datetime.fromisoformat(candidate["completed_at"])
                if candidate["completed_at"]
                else None,
                filepath=candidate["filepath"],
            )
            results.append(result)

        # Cache results
        self.query_cache[cache_key] = results

        return results

    def get_context_suggestions(
        self, context: Dict[str, Any], limit: int = 5
    ) -> List[str]:
        """
        Generate context-aware search suggestions.

        Args:
            context: Current context (current_task, recent_tasks, domain, etc.)
            limit: Maximum suggestions to return

        Returns:
            List of suggested queries
        """
        cache_key = f"suggestions_{hash(str(context))}"

        if cache_key in self.suggestion_cache:
            return self.suggestion_cache[cache_key][:limit]

        suggestions = []

        # Extract context elements
        current_task = context.get("current_task", {})
        domain = context.get("domain", "general")
        task_complexity = context.get("task_complexity", "moderate")

        # Generate suggestions based on current task
        if current_task:
            task_title = current_task.get("title", "")
            task_description = current_task.get("description", "")

            # Get intelligent suggestions based on technical terms
            suggestions.extend(
                self._get_intelligent_suggestions(task_title, domain, task_complexity)
            )

        # Add domain-specific suggestions based on inferred domain
        inferred_domain = self._infer_domain_from_context(current_task, domain)
        domain_suggestions = self._get_domain_suggestions(inferred_domain)
        suggestions.extend(domain_suggestions[:2])

        # Add complexity-based suggestions
        if task_complexity in ["complex", "enterprise"]:
            suggestions.extend(
                [
                    "architecture patterns",
                    "performance optimization",
                    "security best practices",
                ]
            )
        else:
            suggestions.extend(
                ["implementation examples", "quick solutions", "common patterns"]
            )

        # Cache and return unique suggestions
        unique_suggestions = list(
            dict.fromkeys(suggestions)
        )  # Remove duplicates while preserving order
        self.suggestion_cache[cache_key] = unique_suggestions
        return unique_suggestions[:limit]

    def _get_intelligent_suggestions(
        self, task_title: str, domain: str, complexity: str
    ) -> List[str]:
        """Generate intelligent suggestions based on technical terms and context."""
        suggestions = []
        title_lower = task_title.lower()

        # Technology-specific patterns
        tech_patterns = {
            "asgi": [
                "ASGI middleware patterns",
                "FastAPI lifespan events",
                "ASGI application lifecycle",
                "WebSocket transport implementation",
                "ASGI server configuration",
            ],
            "fastapi": [
                "FastAPI dependency injection",
                "API route patterns",
                "Pydantic model validation",
                "FastAPI middleware",
                "async route handlers",
            ],
            "react": [
                "React component patterns",
                "state management solutions",
                "React hooks best practices",
                "component lifecycle optimization",
                "React testing strategies",
            ],
            "auth": [
                "JWT authentication patterns",
                "session management",
                "2FA implementation",
                "OAuth integration",
                "security token handling",
            ],
            "database": [
                "SQLAlchemy async patterns",
                "database migration strategies",
                "query optimization",
                "connection pooling",
                "database indexing",
            ],
            "transport": [
                "transport layer security",
                "async transport patterns",
                "message queue implementation",
                "streaming data handling",
                "transport protocol optimization",
            ],
            "architecture": [
                "hexagonal architecture patterns",
                "dependency injection patterns",
                "repository pattern implementation",
                "microservices architecture",
                "event-driven architecture",
            ],
            "backend": [
                "API design patterns",
                "service layer architecture",
                "async programming patterns",
                "error handling strategies",
                "logging and monitoring",
            ],
            "api": [
                "REST API best practices",
                "GraphQL implementation",
                "API versioning strategies",
                "rate limiting patterns",
                "API documentation",
            ],
            "async": [
                "async/await patterns",
                "concurrent programming",
                "asyncio best practices",
                "async context managers",
                "async database operations",
            ],
            "testing": [
                "pytest async testing",
                "test-driven development",
                "integration testing",
                "mocking strategies",
                "test data management",
            ],
            "security": [
                "authentication patterns",
                "authorization strategies",
                "CORS configuration",
                "input validation",
                "security headers",
            ],
        }

        # Find matching patterns
        for tech, patterns in tech_patterns.items():
            if tech in title_lower:
                suggestions.extend(patterns[:3])  # Take top 3 for each match

        # Generic patterns based on common terms
        if "implement" in title_lower:
            suggestions.extend(
                ["implementation best practices", "common implementation pitfalls"]
            )

        if "optimization" in title_lower or "performance" in title_lower:
            suggestions.extend(["performance monitoring", "optimization techniques"])

        if "security" in title_lower:
            suggestions.extend(["security audit checklist", "vulnerability assessment"])

        # Complexity-based suggestions
        if complexity in ["complex", "enterprise"]:
            suggestions.extend(
                [
                    "architectural decision records",
                    "scalability considerations",
                    "integration patterns",
                ]
            )

        return suggestions[:6]  # Limit to avoid overwhelming

    def _infer_domain_from_context(
        self, current_task: Dict[str, Any], provided_domain: str
    ) -> str:
        """Infer the most appropriate domain from task context."""
        if provided_domain and provided_domain != "general":
            # Check if provided domain makes sense, otherwise infer
            valid_domains = ["backend", "frontend", "security", "devops", "testing"]
            if provided_domain in valid_domains:
                return provided_domain

        # Infer from task title and description
        task_title = current_task.get("title", "").lower()
        task_desc = current_task.get("description", "").lower()
        content = f"{task_title} {task_desc}"

        # Backend indicators
        if any(
            term in content
            for term in ["asgi", "fastapi", "sqlalchemy", "api", "database", "server"]
        ):
            return "backend"

        # Frontend indicators
        if any(
            term in content
            for term in ["react", "typescript", "ui", "component", "frontend"]
        ):
            return "frontend"

        # Security indicators
        if any(
            term in content
            for term in ["auth", "jwt", "security", "2fa", "oauth", "encryption"]
        ):
            return "security"

        # DevOps indicators
        if any(
            term in content
            for term in ["deploy", "docker", "ci", "pipeline", "infrastructure"]
        ):
            return "devops"

        # Testing indicators
        if any(term in content for term in ["test", "pytest", "vitest", "e2e", "unit"]):
            return "testing"

        return provided_domain or "general"

    def _calculate_context_aware_score(
        self,
        similarity: float,
        candidate: Dict[str, Any],
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> float:
        """
        Calculate context-aware hybrid score.
        """
        # Start with base hybrid score
        base_score = self._calculate_hybrid_score(similarity, candidate, query)

        if not context:
            return base_score

        # Apply context-based adjustments
        context_boost = 0.0

        # Task complexity alignment
        current_complexity = context.get("task_complexity", "medium")
        candidate_complexity = self._infer_complexity(candidate)
        if current_complexity == candidate_complexity:
            context_boost += self.context_weights["task_complexity"]

        # Urgency alignment
        current_urgency = context.get("task_urgency", "medium")
        candidate_urgency = self._infer_urgency(candidate)
        if current_urgency == candidate_urgency:
            context_boost += self.context_weights["task_urgency"]

        # Domain relevance
        current_domain = context.get("domain", "general")
        candidate_domain = self._infer_domain(candidate)
        if current_domain == candidate_domain:
            context_boost += self.context_weights["domain_relevance"]

        # Temporal context (prefer recent similar work)
        if context.get("prefer_recent", False):
            recency_factor = self._calculate_recency_factor(candidate)
            context_boost += self.context_weights["temporal_context"] * recency_factor

        return min(1.0, base_score + context_boost)

    def _enhance_query_with_domain_knowledge(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Enhance query with domain-specific knowledge and synonyms.
        """
        if not context:
            return query

        domain = context.get("domain", "general")

        # Domain-specific query enhancements
        domain_mappings = {
            "backend": {
                "api": "fastapi endpoint route",
                "database": "sqlalchemy postgres model",
                "auth": "authentication jwt security",
                "test": "pytest async unittest",
            },
            "frontend": {
                "component": "react typescript jsx",
                "state": "redux toolkit query",
                "ui": "material-ui mui component",
                "test": "vitest react-testing-library",
            },
            "security": {
                "2fa": "two-factor authentication totp",
                "session": "jwt token management",
                "encryption": "gpg security crypto",
            },
        }

        enhanced_terms = []
        query_lower = query.lower()

        if domain in domain_mappings:
            for term, expansion in domain_mappings[domain].items():
                if term in query_lower:
                    enhanced_terms.append(expansion)

        if enhanced_terms:
            return f"{query} {' '.join(enhanced_terms)}"

        return query

    def _generate_context_aware_excerpt(
        self, content: str, query: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate excerpt with context-aware highlighting.
        """
        # Use parent method as base
        base_excerpt = self._generate_excerpt(content, query)

        if not context:
            return base_excerpt

        # Add context-specific highlighting
        current_task = context.get("current_task", {})
        if current_task:
            task_terms = self._extract_key_terms(current_task.get("description", ""))

            # Highlight context-relevant terms
            excerpt = base_excerpt
            for term in task_terms[:3]:
                if term.lower() in excerpt.lower():
                    excerpt = excerpt.replace(term, f"**{term}**")

            return excerpt

        return base_excerpt

    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from text for context analysis."""
        import re

        # Simple keyword extraction (can be enhanced with NLP)
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())

        # Filter common words
        stop_words = {
            "the",
            "and",
            "for",
            "are",
            "but",
            "not",
            "you",
            "all",
            "can",
            "her",
            "was",
            "one",
            "our",
            "had",
            "but",
            "use",
            "day",
            "get",
            "has",
            "him",
            "his",
            "how",
            "man",
            "new",
            "now",
            "old",
            "see",
            "two",
            "way",
            "who",
            "boy",
            "did",
            "its",
            "let",
            "put",
            "say",
            "she",
            "too",
            "use",
        }

        meaningful_words = [w for w in words if w not in stop_words and len(w) > 3]

        # Return most frequent terms
        from collections import Counter

        return [word for word, _ in Counter(meaningful_words).most_common(10)]

    def _infer_complexity(self, candidate: Dict[str, Any]) -> str:
        """Infer task complexity from candidate metadata."""
        content = candidate.get("content", "").lower()

        # Simple heuristics for complexity inference
        if any(
            term in content
            for term in ["enterprise", "advanced", "comprehensive", "complex"]
        ):
            return "high"
        elif any(term in content for term in ["simple", "basic", "quick", "minor"]):
            return "low"
        else:
            return "medium"

    def _infer_urgency(self, candidate: Dict[str, Any]) -> str:
        """Infer task urgency from candidate metadata."""
        content = candidate.get("content", "").lower()

        if any(
            term in content for term in ["urgent", "critical", "emergency", "immediate"]
        ):
            return "high"
        elif any(term in content for term in ["low priority", "when time", "future"]):
            return "low"
        else:
            return "medium"

    def _infer_domain(self, candidate: Dict[str, Any]) -> str:
        """Infer domain from candidate content."""
        content = candidate.get("content", "").lower()

        if any(
            term in content for term in ["fastapi", "sqlalchemy", "pytest", "backend"]
        ):
            return "backend"
        elif any(
            term in content for term in ["react", "typescript", "mui", "frontend"]
        ):
            return "frontend"
        elif any(term in content for term in ["2fa", "jwt", "security", "auth"]):
            return "security"
        else:
            return "general"

    def _calculate_recency_factor(self, candidate: Dict[str, Any]) -> float:
        """Calculate recency factor for temporal context."""
        if not candidate.get("completed_at"):
            return 0.0

        try:
            completed_date = datetime.fromisoformat(candidate["completed_at"])
            days_ago = (datetime.now() - completed_date).days

            # More recent = higher factor
            if days_ago <= 7:
                return 1.0
            elif days_ago <= 30:
                return 0.7
            elif days_ago <= 90:
                return 0.4
            else:
                return 0.1
        except:
            return 0.0

    def _get_domain_suggestions(self, domain: str) -> List[str]:
        """Get domain-specific search suggestions."""
        suggestions_map = {
            "backend": [
                "fastapi patterns",
                "database migrations",
                "api security",
                "async patterns",
            ],
            "frontend": [
                "react components",
                "state management",
                "ui patterns",
                "testing strategies",
            ],
            "security": [
                "2fa implementation",
                "jwt best practices",
                "encryption patterns",
                "security audits",
            ],
            "general": [
                "architecture patterns",
                "best practices",
                "common issues",
                "optimization techniques",
            ],
        }

        return suggestions_map.get(domain, suggestions_map["general"])

    def _get_embedding_similarity(self, query: str, candidate: Dict[str, Any]) -> float:
        """Get embedding similarity between query and candidate."""
        # This would use the existing embedding system
        # Placeholder implementation
        return 0.8  # Would be calculated using actual embeddings


# Enhanced search functions using the new engine
def search_memories_advanced(
    query: str,
    limit: int = 10,
    context: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None,
) -> List[SearchResult]:
    """
    Advanced search with context awareness.
    """
    if db_path is None:
        db_path = get_connection(db_path).db_path

    engine = AdvancedSearchEngine(db_path)
    return engine.search_with_context(query, limit, context)


def get_context_suggestions(
    context: Dict[str, Any], limit: int = 5, db_path: Optional[str] = None
) -> List[str]:
    """
    Get context-aware search suggestions.
    """
    if db_path is None:
        db_path = get_connection(db_path).db_path # Assuming get_connection returns an object with db_path

    engine = AdvancedSearchEngine(db_path)
    return engine.get_context_suggestions(context, limit)


def search_memories(
    query: str,
    k: int = 10,
    kind_filter: Optional[List[str]] = None,
    status_filter: Optional[List[str]] = None,
    db_path: Optional[str] = None,
) -> List[SearchResult]:
    """
    Convenience function for searching memories.

    Args:
        query: Search query text
        k: Number of results to return
        kind_filter: Optional filter by task kinds (string values)
        status_filter: Optional filter by task statuses (string values)
        db_path: Optional database path

    Returns:
        List[SearchResult]: Search results
    """
    engine = SearchEngine(db_path)

    # Convert string filters to enums
    kind_enum_filter = None
    if kind_filter:
        kind_enum_filter = [TaskKind(k) for k in kind_filter]

    status_enum_filter = None
    if status_filter:
        status_enum_filter = [TaskStatus(s) for s in status_filter]

    return engine.search(
        query=query, k=k, kind_filter=kind_enum_filter, status_filter=status_enum_filter
    )


def get_latest_tasks(
    n: int = 10, kind_filter: Optional[List[str]] = None, db_path: Optional[str] = None
) -> List[SearchResult]:
    """
    Get the most recently completed tasks.

    Args:
        n: Number of tasks to return
        kind_filter: Optional filter by task kinds
        db_path: Optional database path

    Returns:
        List[SearchResult]: Latest tasks
    """
    conn = get_connection(db_path)

    where_conditions = []
    params = []

    if kind_filter:
        kind_placeholders = ",".join("?" * len(kind_filter))
        where_conditions.append(f"kind IN ({kind_placeholders})")
        params.extend(kind_filter)

    where_clause = ""
    if where_conditions:
        where_clause = "WHERE " + " AND ".join(where_conditions)

    params.append(n)

    query = f"""
        SELECT task_id, title, kind, status, completed_at, filepath
        FROM archives
        {where_clause}
        ORDER BY completed_at DESC NULLS LAST, created_at DESC
        LIMIT ?
    """

    cursor = conn.execute(query, params)
    results = []

    for row in cursor:
        result = SearchResult(
            task_id=row["task_id"],
            title=row["title"],
            score=1.0,  # Not applicable for latest query
            excerpt="",  # Not needed for latest query
            kind=TaskKind(row["kind"]),
            status=TaskStatus(row["status"]) if row["status"] else None,
            completed_at=datetime.fromisoformat(row["completed_at"])
            if row["completed_at"]
            else None,
            filepath=row["filepath"],
        )
        results.append(result)

    conn.close()
    return results


# ---------------------------------------------------------------------------
# Convenience helper compatible with old CLI
# ---------------------------------------------------------------------------

def create_enhanced_memory(project_root: str = ".") -> "AdvancedSearchEngine":  # noqa: D401
    """Return an AdvancedSearchEngine instance for backward-compat."""
    from serena.infrastructure.database import get_database_path

    return AdvancedSearchEngine(get_database_path())

__all__ = [
    "SearchEngine",
    "AdvancedSearchEngine",
    "search_memories",
    "search_memories_advanced",
    "get_context_suggestions",
    "get_latest_tasks",
    "create_enhanced_memory",
]
