from __future__ import annotations

"""`serena delete` command for removing indexed entries."""

import logging
import sys
from typing import Any, Optional

from serena.core.models import Archive
from serena.database.session import DatabaseManager
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


def _local_delete(task_id: str, db_path: Optional[str] = None) -> bool:
    """Delete entry directly from local database."""
    try:
        db_manager = DatabaseManager(db_path)
        
        with db_manager.get_session() as session:
            # Find the archive entry
            archive = session.query(Archive).filter(Archive.task_id == task_id).first()
            
            if not archive:
                return False
            
            # Delete the archive (embeddings will be cascade deleted)
            session.delete(archive)
            session.commit()
            
            return True
            
    except Exception as exc:
        logging.getLogger(__name__).error("Local delete failed: %s", exc, exc_info=True)
        return False


def _list_entries(limit: int = 20, db_path: Optional[str] = None) -> None:
    """List available entries for reference."""
    try:
        db_manager = DatabaseManager(db_path)
        
        with db_manager.get_session() as session:
            archives = session.query(Archive).order_by(
                Archive.completed_at.desc().nulls_last(),
                Archive.updated_at.desc()
            ).limit(limit).all()
            
            if not archives:
                print("❌ No entries found in database")
                return
            
            print(f"📚 Available entries (showing {len(archives)} most recent):")
            print("-" * 70)
            
            for archive in archives:
                status_str = f" [{archive.status}]" if archive.status else ""
                kind_str = f" ({archive.kind})" if archive.kind else ""
                date_str = f" - {archive.completed_at.date()}" if archive.completed_at else ""
                
                print(f"🆔 {archive.task_id}: {archive.title}{status_str}{kind_str}{date_str}")
                print(f"   📁 {archive.filepath}")
                print()
                
    except Exception as exc:
        logging.getLogger(__name__).error("Failed to list entries: %s", exc, exc_info=True)
        print("❌ Failed to list entries")


def cmd_delete(args) -> None:
    """Delete an indexed entry by task ID."""
    logger = logging.getLogger(__name__)
    
    try:
        # If list flag is provided, show available entries
        if args.list:
            _list_entries(args.limit, getattr(args, 'db_path', None))
            return
        
        if not args.task_id:
            print("❌ Task ID is required. Use --list to see available entries.")
            sys.exit(1)
        
        task_id = args.task_id
        print(f"🗑️  Attempting to delete entry: {task_id}")
        
        # Try server first, then fall back to local
        deleted = False
        
        if _try_server_delete(task_id):
            print("   ⚡ Deleted via server API")
            deleted = True
        else:
            print("   💾 Server not available, trying local database...")
            if _local_delete(task_id, getattr(args, 'db_path', None)):
                print("   ✅ Deleted from local database")
                deleted = True
        
        if deleted:
            print(f"✅ Successfully deleted entry: {task_id}")
            
            # Show remaining entries only if explicitly requested
            if args.show_remaining:
                print("\n📋 Remaining entries:")
                _list_entries(5, getattr(args, 'db_path', None))
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