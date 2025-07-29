from __future__ import annotations

"""`serena index` command."""

import logging
import time
from typing import Any

from serena.cli.common import detect_taskmaster_directories
from serena.infrastructure.indexer import MemoryIndexer


def cmd_index(args) -> None:
    """Index memories from directories."""
    try:
        # Determine directories to scan
        if args.directories:
            directories = [d.strip() for d in args.directories.split(",")]
        else:
            directories = detect_taskmaster_directories()
            if not directories:
                print(
                    "⚠️ No directories found to index. Use --directories to specify manually."
                )
                return

        # Create indexer
        indexer = MemoryIndexer(max_workers=args.workers)

        # Show mode
        print(f"🔍 Indexing directories using server memory: {', '.join(directories)}")

        # Start overall timing
        start_time = time.time()

        stats = indexer.scan_directories(
            directories=directories, force_reindex=args.force, show_progress=True
        )

        total_command_time = time.time() - start_time

        # Display comprehensive results with performance metrics
        print(f"\n✅ Indexing complete!")
        print(f"📁 Directories scanned: {stats['directories_scanned']}")
        print(f"📄 Files found: {stats.get('files_found', 0)}")
        print(f"📄 Files indexed: {stats['files_indexed']}")
        print(f"⏭️ Files skipped: {stats['files_skipped']}")
        if stats["files_failed"] > 0:
            print(f"❌ Files failed: {stats['files_failed']}")

        # Performance metrics
        print("\n⏱️ Performance Summary:")
        scan_time = stats.get("scan_time_seconds", 0)
        indexing_time = stats.get("indexing_time_seconds", 0)
        print(f"   - Directory scan: {scan_time:.2f}s")
        print(f"   - File processing: {indexing_time:.2f}s")
        print(f"   - Total time: {total_command_time:.2f}s")

        # Throughput calculations
        if indexing_time > 0 and stats["files_indexed"] > 0:
            files_per_second = stats["files_indexed"] / indexing_time
            print(f"   - Throughput: {files_per_second:.1f} files/second")

        if stats["files_indexed"] > 0:
            avg_time_per_file = (
                indexing_time / stats["files_indexed"] * 1000
            )  # Convert to ms
            print(f"   - Average per file: {avg_time_per_file:.1f}ms")

        # Efficiency metrics
        total_files = stats.get("files_found", 0)
        if total_files > 0:
            efficiency = (stats["files_indexed"] / total_files) * 100
            print(f"   - Processing efficiency: {efficiency:.1f}%")

        # Ensure proper cleanup of background resources
        _cleanup_indexing_resources(indexer)

    except Exception as e:
        print(f"❌ Indexing failed: {e}")
        raise


def _cleanup_indexing_resources(indexer) -> None:
    """Clean up indexing resources to prevent hanging."""
    try:
        print("⏳ Waiting for server to complete processing...")
        if hasattr(indexer.memory, "wait_for_server_completion"):
            completion_success = indexer.memory.wait_for_server_completion(timeout=10.0)
            if completion_success:
                print("✅ Server processing completed")
            else:
                print(
                    "⚠️ Timeout waiting for server - some operations may still be processing"
                )

        # Close HTTP connections
        if hasattr(indexer.memory, "close"):
            indexer.memory.close()
            print("✅ Remote connections closed")

        # No cleanup needed for RemoteMemory - it just makes HTTP requests

    except Exception as e:
        # Don't let cleanup errors prevent command completion
        print(f"⚠️ Cleanup warning: {e}")
        pass


def register(sub: Any) -> None:
    """Register the index command."""
    p = sub.add_parser("index", help="Scan directories and index memories")
    p.add_argument("--directories", help="Comma-separated directories to scan")
    p.add_argument("--force", action="store_true", help="Force reindex")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("-v", "--verbose", action="store_true")
    p.set_defaults(func=cmd_index)
