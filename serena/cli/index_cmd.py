from __future__ import annotations

"""`serena index` command."""

import logging
from typing import Any

from serena.cli.common import detect_taskmaster_directories
from serena.infrastructure.indexer import MemoryIndexer


def cmd_index(args) -> None:
    """Index memories from directories."""
    logger = logging.getLogger(__name__)
    
    try:
        # Determine directories to scan
        if args.directories:
            directories = [d.strip() for d in args.directories.split(",")]
        else:
            directories = detect_taskmaster_directories()
            if not directories:
                logger.warning("No TaskMaster directories found. Use --directories to specify manually.")
                print("⚠️ No directories found to index. Use --directories to specify manually.")
                return
        
        # Create indexer with server preference
        use_server = not getattr(args, 'local_only', False)  # Default to server unless --local-only
        indexer = MemoryIndexer(max_workers=args.workers, use_server=use_server)
        
        # Show which mode we're using
        memory_type = "server" if hasattr(indexer.memory, 'server_url') else "local"
        print(f"🔍 Indexing directories using {memory_type} memory: {', '.join(directories)}")
        
        stats = indexer.scan_directories(
            directories=directories,
            force_reindex=args.force,
            show_progress=True
        )
        
        print(f"\n✅ Indexing complete!")
        print(f"📁 Directories scanned: {stats['directories_scanned']}")
        print(f"📄 Files indexed: {stats['files_indexed']}")
        print(f"⏭️ Files skipped: {stats['files_skipped']}")
        if stats['files_failed'] > 0:
            print(f"❌ Files failed: {stats['files_failed']}")
        
    except Exception as e:
        logger.error(f"Indexing failed: {e}")
        print(f"❌ Indexing failed: {e}")
        raise


def register(sub: Any) -> None:
    """Register the index command."""
    p = sub.add_parser("index", help="Scan directories and index memories")
    p.add_argument("--directories", help="Comma-separated directories to scan")
    p.add_argument("--force", action="store_true", help="Force reindex")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--local-only", action="store_true", help="Use local memory only, don't try server")
    p.add_argument("-v", "--verbose", action="store_true")
    p.set_defaults(func=cmd_index)