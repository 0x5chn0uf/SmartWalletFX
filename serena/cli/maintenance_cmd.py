from __future__ import annotations

"""Background maintenance operations for the Serena memory system."""

import logging
import sys
import time
from typing import Any, Dict, List, Optional

from serena.database.session import get_db_session
from serena.core.models import Archive, Embedding
from serena.infrastructure.write_queue import write_queue, WriteOperationType
from serena.services.memory_impl import Memory
from serena.settings import settings

logger = logging.getLogger(__name__)


def _cleanup_orphaned_embeddings(db_path: Optional[str] = None) -> Dict[str, int]:
    """Clean up embeddings that have no corresponding archive entries."""
    stats = {"removed": 0, "checked": 0}
    
    try:
        with get_db_session(db_path or settings.memory_db) as session:
            # Find embeddings with no matching archive
            orphaned = session.query(Embedding).filter(
                ~Embedding.task_id.in_(
                    session.query(Archive.task_id)
                )
            ).all()
            
            stats["checked"] = session.query(Embedding).count()
            
            if orphaned:
                logger.info(f"Found {len(orphaned)} orphaned embeddings")
                
                for embedding in orphaned:
                    session.delete(embedding)
                    stats["removed"] += 1
                
                logger.info(f"Removed {stats['removed']} orphaned embeddings")
            
    except Exception as exc:
        logger.error("Failed to cleanup orphaned embeddings: %s", exc)
        
    return stats


def _compact_database(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Compact the database to reclaim space."""
    stats = {"success": False, "size_before": 0, "size_after": 0}
    
    db_file = db_path or settings.memory_db
    
    try:
        import os
        from serena.infrastructure.database import checkpoint_database
        
        # Get size before
        if os.path.exists(db_file):
            stats["size_before"] = os.path.getsize(db_file)
        
        # Perform checkpoint and vacuum
        checkpoint_database(db_file)
        
        with get_db_session(db_file) as session:
            session.execute("VACUUM")
        
        # Get size after
        if os.path.exists(db_file):
            stats["size_after"] = os.path.getsize(db_file)
        
        stats["success"] = True
        logger.info("Database compaction completed")
        
    except Exception as exc:
        logger.error("Database compaction failed: %s", exc)
        
    return stats


def _rebuild_missing_embeddings(db_path: Optional[str] = None, batch_size: int = 50) -> Dict[str, int]:
    """Rebuild embeddings for archives that are missing them."""
    stats = {"processed": 0, "updated": 0, "failed": 0}
    
    try:
        memory = Memory(db_path=db_path)
        
        with get_db_session(db_path or settings.memory_db) as session:
            # Find archives without embeddings
            archives_without_embeddings = session.query(Archive).filter(
                ~Archive.task_id.in_(
                    session.query(Embedding.task_id).distinct()
                )
            ).all()
            
            logger.info(f"Found {len(archives_without_embeddings)} archives without embeddings")
            
            # Process in batches
            for i in range(0, len(archives_without_embeddings), batch_size):
                batch = archives_without_embeddings[i:i + batch_size]
                
                for archive in batch:
                    stats["processed"] += 1
                    
                    try:
                        # Read the archive content from file if available
                        content = None
                        if archive.filepath:
                            try:
                                with open(archive.filepath, 'r', encoding='utf-8') as f:
                                    content = f.read()
                            except Exception:
                                # Use summary as fallback
                                content = archive.summary or f"Archive: {archive.title}"
                        else:
                            content = archive.summary or f"Archive: {archive.title}"
                        
                        if content:
                            # Re-upsert to generate embeddings
                            success = memory.upsert(
                                task_id=archive.task_id,
                                markdown_text=content,
                                filepath=archive.filepath,
                                title=archive.title,
                                kind=archive.kind,
                                status=archive.status,
                                completed_at=archive.completed_at,
                                async_write=False  # Use sync for maintenance
                            )
                            
                            if success:
                                stats["updated"] += 1
                            else:
                                stats["failed"] += 1
                                
                    except Exception as exc:
                        logger.warning(f"Failed to rebuild embeddings for {archive.task_id}: {exc}")
                        stats["failed"] += 1
                
                logger.info(f"Processed batch {i//batch_size + 1}: {len(batch)} archives")
        
    except Exception as exc:
        logger.error("Failed to rebuild embeddings: %s", exc)
        
    return stats


def _maintenance_cleanup_operation() -> Dict[str, Any]:
    """Main maintenance operation that combines multiple cleanup tasks."""
    start_time = time.time()
    results = {
        "start_time": start_time,
        "operations": {},
        "success": True
    }
    
    try:
        logger.info("Starting maintenance cleanup operation")
        
        # 1. Cleanup orphaned embeddings
        logger.info("Step 1: Cleaning up orphaned embeddings")
        results["operations"]["cleanup_orphaned"] = _cleanup_orphaned_embeddings()
        
        # 2. Rebuild missing embeddings
        logger.info("Step 2: Rebuilding missing embeddings")
        results["operations"]["rebuild_embeddings"] = _rebuild_missing_embeddings()
        
        # 3. Compact database
        logger.info("Step 3: Compacting database")
        results["operations"]["compact_database"] = _compact_database()
        
        results["end_time"] = time.time()
        results["duration"] = results["end_time"] - start_time
        
        logger.info(f"Maintenance cleanup completed in {results['duration']:.2f}s")
        
    except Exception as exc:
        logger.error(f"Maintenance operation failed: {exc}")
        results["success"] = False
        results["error"] = str(exc)
        
    return results


def _schedule_maintenance_async() -> str:
    """Schedule maintenance operation through write queue."""
    try:
        operation_id = write_queue.submit(
            _maintenance_cleanup_operation,
            priority=3,  # Lower priority than regular operations
            operation_type=WriteOperationType.MAINTENANCE,
        )
        
        logger.info(f"Scheduled maintenance operation with ID: {operation_id}")
        return operation_id
        
    except Exception as exc:
        logger.error(f"Failed to schedule maintenance operation: {exc}")
        raise


def cmd_maintenance(args) -> None:
    """Perform maintenance operations on the memory database."""
    logger.info("Starting maintenance operation")
    
    try:
        if args.operation == "cleanup":
            if args.async_mode and settings.async_write:
                print("🔧 Scheduling maintenance cleanup operation...")
                operation_id = _schedule_maintenance_async()
                print(f"⏳ Maintenance operation queued with ID: {operation_id}")
                print("   Check logs for completion status")
            else:
                print("🔧 Running maintenance cleanup operation...")
                start_time = time.time()
                
                results = _maintenance_cleanup_operation()
                
                # Display results
                print(f"\n📊 Maintenance Results:")
                print(f"   Duration: {results.get('duration', 0):.2f}s")
                print(f"   Success: {'✅' if results['success'] else '❌'}")
                
                if 'operations' in results:
                    ops = results['operations']
                    
                    if 'cleanup_orphaned' in ops:
                        clean = ops['cleanup_orphaned']
                        print(f"   Orphaned embeddings: {clean['removed']}/{clean['checked']} removed")
                    
                    if 'rebuild_embeddings' in ops:
                        rebuild = ops['rebuild_embeddings']
                        print(f"   Missing embeddings: {rebuild['updated']}/{rebuild['processed']} rebuilt")
                    
                    if 'compact_database' in ops:
                        compact = ops['compact_database']
                        if compact['success']:
                            size_saved = compact['size_before'] - compact['size_after']
                            print(f"   Database size: {size_saved:,} bytes saved")
                        else:
                            print("   Database compaction: failed")
                
                if results['success']:
                    print("✅ Maintenance operation completed successfully!")
                else:
                    print(f"❌ Maintenance operation failed: {results.get('error', 'Unknown error')}")
                    sys.exit(1)
        
        elif args.operation == "status":
            print("📊 Write Queue Status:")
            health = write_queue.health_check()
            metrics = write_queue.get_metrics()
            
            print(f"   Status: {health['status']} (score: {health['health_score']}/100)")
            if health['issues']:
                for issue in health['issues']:
                    print(f"   ⚠️  {issue}")
            
            print(f"   Queue size: {metrics.current_queue_size}")
            print(f"   Total operations: {metrics.total_operations}")
            print(f"   Success rate: {metrics.successful_operations}/{metrics.total_operations}")
            print(f"   Avg processing time: {metrics.avg_processing_time_ms:.2f}ms")
            
        else:
            print(f"❌ Unknown maintenance operation: {args.operation}")
            print("   Available operations: cleanup, status")
            sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n🛑 Maintenance operation cancelled by user")
        sys.exit(1)
    except Exception:
        logger.exception("Maintenance operation failed")
        print("❌ Maintenance failed: unexpected error. See logs for details.")
        sys.exit(1)
    
    finally:
        # Shutdown write queue to prevent hanging
        try:
            shutdown_success = write_queue.shutdown(timeout=5.0)
            if shutdown_success:
                logger.debug("✅ Write queue shutdown completed")
            else:
                logger.debug("⚠️ Write queue shutdown timeout")
        except Exception as queue_e:
            logger.debug(f"Write queue cleanup warning: {queue_e}")


def register(sub: Any) -> None:
    """Register the maintenance command."""
    p = sub.add_parser("maintenance", help="Perform maintenance operations on the memory database")
    p.add_argument("operation", choices=["cleanup", "status"], 
                   help="Maintenance operation to perform")
    p.add_argument("--async", dest="async_mode", action="store_true", 
                   help="Run maintenance operation asynchronously via write queue")
    p.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    p.set_defaults(func=cmd_maintenance)