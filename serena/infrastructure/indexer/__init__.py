from __future__ import annotations

"""Indexer package  – consolidates indexing-related code.

External code can continue to do ``from serena.infrastructure.indexer import
MemoryIndexer`` because this package re-exports the symbols from
:pyfile:`core.py`.
"""

from importlib import import_module as _import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover – static analysers
    from .core import MemoryIndexer, index_memories, index_memories_async
else:
    _core = _import_module("serena.infrastructure.indexer.core")
    MemoryIndexer = _core.MemoryIndexer  # type: ignore[attr-defined]
    index_memories = _core.index_memories  # type: ignore[attr-defined]
    index_memories_async = _core.index_memories_async  # type: ignore[attr-defined]

__all__ = [
    "MemoryIndexer",
    "index_memories",
    "index_memories_async",
] 