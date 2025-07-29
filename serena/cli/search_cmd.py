from __future__ import annotations

"""`serena search` and related sub-commands."""

import logging
import sys
from typing import Any

from serena.settings import settings
from serena.core.errors import SerenaException, get_user_friendly_message, ErrorCode




def _try_server_search(query: str, limit: int):
    """Try to use server API for search with structured error handling."""
    remote_memory = None
    try:
        from serena.cli.common import RemoteMemory
        
        remote_memory = RemoteMemory()
        if not remote_memory.is_server_available():
            error_info = remote_memory.get_server_error_info()
            if error_info:
                logging.getLogger(__name__).error(
                    "Server unavailable - %s: %s", 
                    error_info['code'], 
                    error_info['message']
                )
                if error_info.get('details'):
                    logging.getLogger(__name__).debug("Error details: %s", error_info['details'])
            return [], False, error_info
        
        # Perform search using RemoteMemory (which handles structured errors)
        results_data = remote_memory.search(query, limit)
        
        # Convert API response to SearchResult objects
        from serena.core.models import SearchResult, TaskKind, TaskStatus
        from datetime import datetime
        
        results = []
        for item in results_data:
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
        
        return results, True, None  # Success
        
    except Exception as exc:
        logging.getLogger(__name__).debug("Server search failed: %s", exc, exc_info=True)
        
        # Extract error info if it's a structured error
        error_info = None
        if isinstance(exc, SerenaException):
            error_info = {
                'code': exc.code.value,
                'message': exc.message,
                'details': exc.details
            }
        
        return [], False, error_info  # Failed
    
    finally:
        # Cleanup connections to prevent hanging
        if remote_memory:
            try:
                # Wait for server completion and close connections
                remote_memory.wait_for_server_completion(timeout=5.0)
                remote_memory.close()
            except Exception as cleanup_e:
                logging.getLogger(__name__).debug(f"Cleanup warning: {cleanup_e}")
        
        # Shutdown write queue to prevent hanging
        try:
            from serena.infrastructure.write_queue import write_queue
            shutdown_success = write_queue.shutdown(timeout=5.0)
            if shutdown_success:
                logging.getLogger(__name__).debug("✅ Write queue shutdown completed")
            else:
                logging.getLogger(__name__).debug("⚠️ Write queue shutdown timeout")
        except ImportError:
            # Write queue not available - normal for some configurations
            pass
        except Exception as queue_e:
            logging.getLogger(__name__).debug(f"Write queue cleanup warning: {queue_e}")


def cmd_search(args) -> None:
    """Search memories using semantic search with structured error handling."""
    logger = logging.getLogger(__name__)
    
    try:
        print(f"🔍 Searching for: '{args.query}'")
        
        # Validate query
        if not args.query or len(args.query.strip()) == 0:
            print("❌ Error: Search query cannot be empty")
            print("   Please provide a search term")
            sys.exit(1)
        
        if len(args.query) > 500:
            print("❌ Error: Search query too long (max 500 characters)")
            sys.exit(1)
        
        results, server_success, error_info = _try_server_search(args.query, args.limit)
        
        if server_success:
            print("   ⚡ Using server API (preloaded model)")
        else:
            print("❌ Serena server not available or search failed")
            
            if error_info:
                # Display user-friendly error message using the simplified system
                error_code = ErrorCode(error_info['code'])
                friendly_message = get_user_friendly_message(error_code, error_info['message'])
                print(f"   {friendly_message}")
                
                if args.verbose and error_info.get('details'):
                    print(f"   Details: {error_info['details']}")
            else:
                print("   💡 Solution: Start the server with: serena serve")
            
            sys.exit(1)
        
        if not results:
            print("❌ No results found")
            print(f"   Try different keywords or check if content is indexed")
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
        print("   💡 Solution: Install required dependencies")
        sys.exit(1)
    except Exception as e:
        logger.exception("Search failed")
        print(f"❌ Search failed: {str(e)}")
        print("   💡 Solution: Check logs for details or report this issue")
        sys.exit(1)


def register(sub: Any) -> None:
    """Register the search command."""
    p = sub.add_parser("search", help="Semantic search across memories")
    p.add_argument("query", help="Query string")
    p.add_argument("--limit", type=int, default=10, help="Number of results to return")
    p.add_argument("--advanced", action="store_true", help="Use advanced mode")
    p.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    p.set_defaults(func=cmd_search)