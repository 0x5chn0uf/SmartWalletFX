"""Latest command for showing recent archives."""

import logging
from typing import Any

from serena.cli.common import RemoteMemory
from serena.services.memory_impl import Memory


def cmd_latest(args) -> None:
    """Show latest archives."""
    logger = logging.getLogger(__name__)
    
    try:
        # Try server first, fallback to local
        use_server = not getattr(args, 'local_only', False)
        
        if use_server:
            try:
                remote_memory = RemoteMemory()
                if remote_memory.is_server_available():
                    # Use server API
                    response = remote_memory._make_request('GET', '/archives', params={
                        'limit': args.limit,
                        'offset': 0
                    })
                    archives = response.get('archives', [])
                    memory_type = "server"
                else:
                    # Fallback to local
                    memory = Memory()
                    archives = memory.latest(n=args.limit)
                    memory_type = "local"
            except Exception as e:
                logger.warning(f"Failed to connect to server: {e}")
                memory = Memory()
                archives = memory.latest(n=args.limit)
                memory_type = "local"
        else:
            memory = Memory()
            archives = memory.latest(n=args.limit)
            memory_type = "local"
        
        if not archives:
            print("📭 No archives found")
            return
        
        # Display header
        if getattr(args, 'verbose', False):
            print(f"🔍 Using {memory_type} memory")
        
        print(f"📚 Latest {len(archives)} archives:")
        print()
        
        # Display archives
        for i, archive in enumerate(archives, 1):
            # Handle both server API format and local Memory format
            if hasattr(archive, 'task_id'):
                # Local Memory result format (SearchResult object)
                task_id = archive.task_id
                title = archive.title
                kind = archive.kind.value if hasattr(archive.kind, 'value') else str(archive.kind)
                status = archive.status.value if hasattr(archive.status, 'value') else str(archive.status) if archive.status else None
                completed_at = archive.completed_at.isoformat() if archive.completed_at else None
                created_at = None  # SearchResult doesn't have created_at
                filepath = archive.filepath
            else:
                # Server API result format
                task_id = archive.get('task_id')
                title = archive.get('title')
                kind = archive.get('kind')
                status = archive.get('status')
                completed_at = archive.get('completed_at')
                created_at = archive.get('created_at')
                filepath = archive.get('filepath', 'N/A')
            
            print(f"{i:2d}. 📄 {task_id}")
            print(f"    📝 {title}")
            
            if kind:
                print(f"    🏷️  {kind}", end="")
                if status:
                    print(f" | 📊 {status}", end="")
                print()
            
            if completed_at:
                print(f"    ✅ Completed: {completed_at}")
            elif created_at:
                print(f"    📅 Created: {created_at}")
            
            if getattr(args, 'show_path', False):
                print(f"    📁 {filepath}")
            
            print()
        
        # Show total count if using server
        if memory_type == "server" and 'response' in locals():
            total = response.get('total', len(archives))
            if total > len(archives):
                print(f"📊 Showing {len(archives)} of {total} total archives")
    
    except Exception as e:
        logger.error(f"Failed to get latest archives: {e}")
        print(f"❌ Failed to get latest archives: {e}")


def register(sub: Any) -> None:
    """Register the latest command."""
    p = sub.add_parser("latest", help="Show latest archives")
    p.add_argument("-n", "--limit", type=int, default=10, help="Number of recent archives to show (default: 10)")
    p.add_argument("--show-path", action="store_true", help="Show file paths")
    p.add_argument("--local-only", action="store_true", help="Use local memory only")
    p.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    p.set_defaults(func=cmd_latest)