from __future__ import annotations

"""`serena search` and related sub-commands."""

import logging
import sys
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
            print(f"{i}. [{result.task_id}] {result.title}")
            if result.filepath:
                print(f"   📁 {result.filepath}")
            if result.kind:
                print(f"   🏷️ {result.kind.value}")
            if result.score:
                print(f"   📊 Score: {result.score:.3f}")
            if result.excerpt:
                print(f"   📝 {result.excerpt[:100]}...")
            print()
        
    except KeyboardInterrupt:
        print("\n🛑 Search cancelled by user")
        sys.exit(1)
    except ImportError as e:
        logger.error("Missing dependency: %s", e)
        print(f"❌ Missing dependency: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error("Search failed: %s", e)
        print(f"❌ Search failed: {e}")
        sys.exit(1)


def register(sub: Any) -> None:
    """Register the search command."""
    p = sub.add_parser("search", help="Semantic search across memories")
    p.add_argument("query", help="Query string")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--advanced", action="store_true", help="Use advanced mode")
    p.add_argument("-v", "--verbose", action="store_true")
    p.set_defaults(func=cmd_search)