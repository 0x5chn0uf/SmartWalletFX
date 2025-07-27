from __future__ import annotations

"""`serena search` and related sub-commands."""

import logging
from typing import Any

from serena.services.memory_impl import Memory


def cmd_search(args) -> None:
    """Search memories using semantic search."""
    logger = logging.getLogger(__name__)
    
    try:
        memory = Memory()
        
        print(f"🔍 Searching for: '{args.query}'")
        results = memory.search(
            query=args.query,
            k=args.limit
        )
        
        if not results:
            print("❌ No results found")
            return
        
        print(f"\n✅ Found {len(results)} results:")
        print("-" * 50)
        
        for i, result in enumerate(results, 1):
            score = result.get('score', 0)
            task_id = result.get('task_id', 'unknown')
            title = result.get('title', 'Untitled')
            filepath = result.get('filepath', '')
            kind = result.get('kind', '')
            
            print(f"{i}. [{task_id}] {title}")
            if filepath:
                print(f"   📁 {filepath}")
            if kind:
                print(f"   🏷️ {kind}")
            if score:
                print(f"   📊 Score: {score:.3f}")
            print()
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        print(f"❌ Search failed: {e}")
        raise


def register(sub: Any) -> None:
    """Register the search command."""
    p = sub.add_parser("search", help="Semantic search across memories")
    p.add_argument("query", help="Query string")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--advanced", action="store_true", help="Use advanced mode")
    p.add_argument("-v", "--verbose", action="store_true")
    p.set_defaults(func=cmd_search)