from __future__ import annotations

"""`serena delete` command for removing indexed entries."""

import logging
import sys
from typing import Any, Optional

from serena.settings import settings


def _try_server_delete(task_id: str) -> bool:
    """Try to use server API for deletion if server is running."""
    import requests
    # consolidated settings
    server_url = settings.server_url
    
    try:
        response = requests.delete(
            f"{server_url}/archives/{task_id}",
            timeout=5
        )
        return response.status_code == 200
    except Exception as exc:
        logging.getLogger(__name__).debug("Server delete failed: %s", exc, exc_info=True)
    
    return False




def _list_entries_remote(limit: int = 20) -> None:
    """List available entries via server API."""
    remote_memory = None
    try:
        from serena.cli.common import RemoteMemory
        
        remote_memory = RemoteMemory()
        if not remote_memory.is_server_available():
            print("❌ Server not available - cannot list entries")
            return
        
        # Get archives via server API
        response = remote_memory._make_request('GET', '/archives', params={
            'limit': limit,
            'offset': 0
        })
        archives = response.get('archives', [])
        
        if not archives:
            print("📭 No entries found")
            return
        
        print(f"📚 Available entries (showing {len(archives)} most recent):")
        print("-" * 70)
        
        for archive in archives:
            status_str = f" [{archive.get('status')}]" if archive.get('status') else ""
            kind_str = f" ({archive.get('kind')})" if archive.get('kind') else ""
            date_str = f" - {archive.get('completed_at', '').split('T')[0]}" if archive.get('completed_at') else ""
            
            print(f"🆔 {archive.get('task_id')}: {archive.get('title')}{status_str}{kind_str}{date_str}")
            print(f"   📁 {archive.get('filepath', 'N/A')}")
            print()
            
    except Exception as exc:
        logging.getLogger(__name__).error("Failed to list entries: %s", exc, exc_info=True)
        print("❌ Failed to list entries")
    
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


def cmd_delete(args) -> None:
    """Delete an indexed entry by task ID."""
    logger = logging.getLogger(__name__)
    
    try:
        # If list flag is provided, show available entries via server
        if args.list:
            _list_entries_remote(args.limit)
            return
        
        if not args.task_id:
            print("❌ Task ID is required. Use --list to see available entries.")
            sys.exit(1)
        
        task_id = args.task_id
        print(f"🗑️  Attempting to delete entry: {task_id}")
        
        # Server mode only - fail if server not available
        deleted = False
        
        if _try_server_delete(task_id):
            print("   ⚡ Deleted via server API")
            deleted = True
        else:
            print("❌ Server not available - only remote operations are supported")
            sys.exit(1)
        
        if deleted:
            print(f"✅ Successfully deleted entry: {task_id}")
            
            # Show remaining entries only if explicitly requested
            if args.show_remaining:
                print("\n📋 Remaining entries:")
                _list_entries_remote(5)
        else:
            print(f"❌ Entry not found or could not be deleted: {task_id}")
            print("   Use --list to see available entries")
            sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n🛑 Delete operation cancelled by user")
        sys.exit(1)
    except Exception:
        logger.exception("Delete operation failed")
        print("❌ Delete operation failed: unexpected error. See logs for details.")
        sys.exit(1)


def register(sub: Any) -> None:
    """Register the delete command."""
    p = sub.add_parser("delete", help="Delete indexed entries by task ID")
    p.add_argument("task_id", nargs="?", help="Task ID to delete")
    p.add_argument("--list", action="store_true", help="List available entries")
    p.add_argument("--limit", type=int, default=20, help="Number of entries to show when listing")
    p.add_argument("--show-remaining", action="store_true", help="Show remaining entries after deletion")
    p.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    p.set_defaults(func=cmd_delete)