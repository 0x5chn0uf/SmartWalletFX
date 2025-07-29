from __future__ import annotations

"""Background maintenance operations for the Serena memory system."""

import logging
import sys
import time
from typing import Any, Dict, List, Optional

from serena.infrastructure.write_queue import write_queue

logger = logging.getLogger(__name__)


# All maintenance operations have been moved to server-side only
# Local database maintenance is no longer supported


def cmd_maintenance(args) -> None:
    """Perform maintenance operations via server API."""
    logger.info("Starting maintenance operation")
    
    try:
        if args.operation == "cleanup":
            print("❌ Local maintenance is no longer supported.")
            print("   All maintenance operations must be performed through the server.")
            print("   Use the server API endpoints or wait for automatic maintenance.")
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
            print("   Available operations: status")
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
    p = sub.add_parser("maintenance", help="Show maintenance and queue status")
    p.add_argument("operation", choices=["status"], 
                   help="Maintenance operation to perform")
    p.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    p.set_defaults(func=cmd_maintenance)