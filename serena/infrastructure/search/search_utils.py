"""Search utility functions and convenience wrappers."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from serena.core.models import SearchResult, TaskKind, TaskStatus
from serena.infrastructure.database import get_connection
from serena.infrastructure.search.search_core import SearchEngine


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


def create_enhanced_memory(project_root: str = ".") -> SearchEngine:
    """Return a SearchEngine instance for backward-compat."""
    from serena.infrastructure.database import get_database_path
    
    return SearchEngine(get_database_path())