from __future__ import annotations

"""Search package  – provides semantic search engine wrappers."""

from importlib import import_module as _import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .engine import (
        SearchEngine,
        AdvancedSearchEngine,
        search_memories,
        search_memories_advanced,
        get_context_suggestions,
        get_latest_tasks,
    )
else:
    _engine = _import_module("serena.infrastructure.search.engine")

    SearchEngine = _engine.SearchEngine  # type: ignore[attr-defined]
    AdvancedSearchEngine = _engine.AdvancedSearchEngine  # type: ignore[attr-defined]
    search_memories = _engine.search_memories  # type: ignore[attr-defined]
    search_memories_advanced = _engine.search_memories_advanced  # type: ignore[attr-defined]
    get_context_suggestions = _engine.get_context_suggestions  # type: ignore[attr-defined]
    get_latest_tasks = _engine.get_latest_tasks  # type: ignore[attr-defined]

__all__ = [
    "SearchEngine",
    "AdvancedSearchEngine",
    "search_memories",
    "search_memories_advanced",
    "get_context_suggestions",
    "get_latest_tasks",
] 