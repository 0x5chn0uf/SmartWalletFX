from __future__ import annotations

"""Background maintenance operations for the Serena memory system."""

import logging
import sys
import time
from typing import Any, Dict, List, Optional

from serena.cli.common import RemoteMemory


# All maintenance operations have been moved to server-side only
# Local database maintenance is no longer supported


def cmd_maintenance(args) -> None:
    """Perform maintenance operations via server API."""
    print("Starting maintenance operation")

    try:
        if args.operation == "cleanup":
            print("❌ Local maintenance is no longer supported.")
            print("   All maintenance operations must be performed through the server.")
            print("   Use the server API endpoints or wait for automatic maintenance.")
            sys.exit(1)

        elif args.operation == "status":
            print("📊 Server Status:")
            try:
                remote_memory = RemoteMemory()
                if not remote_memory.is_server_available():
                    print("   ❌ Server not available")
                    print("   💡 Start the server with: serena serve")
                    return

                # Get server health status
                health_response = remote_memory._make_request("GET", "/health")
                print(f"   Status: {health_response.get('status', 'unknown')}")

                # Get maintenance status if available
                try:
                    maintenance_response = remote_memory._make_request(
                        "GET", "/maintenance/status"
                    )
                    if "health" in maintenance_response:
                        health_info = maintenance_response["health"]
                        print(
                            f"   Database size: {health_info.get('database_size', 0) / (1024*1024):.1f} MB"
                        )
                        print(
                            f"   Archive count: {health_info.get('archive_count', 0)}"
                        )
                        print(
                            f"   Embedding count: {health_info.get('embedding_count', 0)}"
                        )
                except Exception:
                    print("   Maintenance info not available")

            except Exception as e:
                print(f"   ❌ Failed to get server status: {e}")

        else:
            print(f"❌ Unknown maintenance operation: {args.operation}")
            print("   Available operations: status")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n🛑 Maintenance operation cancelled by user")
        sys.exit(1)
    except Exception:
        print("❌ Maintenance failed: unexpected error. See logs for details.")
        sys.exit(1)


def register(sub: Any) -> None:
    """Register the maintenance command."""
    p = sub.add_parser("maintenance", help="Show maintenance and queue status")
    p.add_argument(
        "operation", choices=["status"], help="Maintenance operation to perform"
    )
    p.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    p.set_defaults(func=cmd_maintenance)
