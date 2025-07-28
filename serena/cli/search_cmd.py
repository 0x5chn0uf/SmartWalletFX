from __future__ import annotations

"""`serena search` and related sub-commands."""

import logging
import sys
from typing import Any




def _try_server_search(query: str, limit: int):
    """Try to use server API for search if server is running."""
    import requests
    from serena import config
    
    try:
        server_url = config.server_url()
        response = requests.get(
            f"{server_url}/search",
            params={"q": query, "limit": limit},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            
            # Convert API response to SearchResult objects
            from serena.core.models import SearchResult, TaskKind, TaskStatus
            from datetime import datetime
            
            results = []
            for item in data.get("results", []):
                result = SearchResult(
                    task_id=item["task_id"],
                    title=item["title"],
                    score=item["score"],
                    excerpt=item["excerpt"],
                    kind=TaskKind(item["kind"]) if item["kind"] else None,
                    status=TaskStatus(item["status"]) if item["status"] else None,
                    completed_at=datetime.fromisoformat(item["completed_at"]) if item["completed_at"] else None,
                    filepath=item["filepath"]
                )
                results.append(result)
            
            return results, True  # Success
    except Exception as exc:
        logging.getLogger(__name__).debug("Server search failed: %s", exc, exc_info=True)
    
    return [], False  # Failed


def cmd_search(args) -> None:
    """Search memories using semantic search."""
    logger = logging.getLogger(__name__)
    
    try:
        print(f"🔍 Searching for: '{args.query}'")
        results, server_success = _try_server_search(args.query, args.limit)
        
        if server_success:
            print("   ⚡ Using server API (preloaded model)")
        else:
            print("❌ Serena server not available or semantic search disabled.")
            print("   Start the server with: serena serve")
            sys.exit(1)
        
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
    except Exception:
        logger.exception("Search failed")
        print("❌ Search failed: unexpected error. See logs for details.")
        sys.exit(1)


def register(sub: Any) -> None:
    """Register the search command."""
    p = sub.add_parser("search", help="Semantic search across memories")
    p.add_argument("query", help="Query string")
    p.add_argument("--limit", type=int, default=10, help="Number of results to return")
    p.add_argument("--advanced", action="store_true", help="Use advanced mode")
    p.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    p.set_defaults(func=cmd_search)