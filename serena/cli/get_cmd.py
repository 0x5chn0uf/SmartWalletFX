"""Get command for retrieving specific archives."""

import logging
from typing import Any

from serena.cli.common import RemoteMemory


def cmd_get(args) -> None:
    """Get specific archive by task ID."""
    logger = logging.getLogger(__name__)
    remote_memory = None
    
    if not args.task_id:
        print("❌ Task ID is required")
        return
    
    try:
        # Remote-only mode - fail if server not available
        remote_memory = RemoteMemory()
        if not remote_memory.is_server_available():
            print("❌ Server not available - remote operations only")
            return
        
        memory = remote_memory
        memory_type = "server"
        
        # Get the archive
        result = memory.get(args.task_id)
        
        if not result:
            print(f"❌ Archive not found: {args.task_id}")
            return
        
        # Display the result
        if getattr(args, 'verbose', False):
            print(f"🔍 Using {memory_type} memory")
        
        print(f"📄 Task ID: {result.get('task_id', args.task_id)}")
        print(f"📝 Title: {result.get('title', 'N/A')}")
        print(f"📁 File: {result.get('filepath', 'N/A')}")
        
        if result.get('kind'):
            print(f"🏷️  Kind: {result.get('kind')}")
        if result.get('status'):
            print(f"📊 Status: {result.get('status')}")
        if result.get('completed_at'):
            print(f"✅ Completed: {result.get('completed_at')}")
        if result.get('created_at'):
            print(f"📅 Created: {result.get('created_at')}")
        if result.get('updated_at'):
            print(f"🔄 Updated: {result.get('updated_at')}")
        
        # Show summary if available
        if result.get('summary'):
            print(f"\n📋 Summary:")
            print(result.get('summary'))
        
        # Show content if requested
        if getattr(args, 'content', False):
            if result.get('filepath'):
                try:
                    with open(result.get('filepath'), 'r', encoding='utf-8') as f:
                        content = f.read()
                    print(f"\n📖 Content:")
                    print("-" * 50)
                    print(content)
                except Exception as e:
                    print(f"⚠️  Could not read content from {result.get('filepath')}: {e}")
            else:
                print("⚠️  No filepath available for content display")
        
    except Exception as e:
        logger.error(f"Failed to get archive {args.task_id}: {e}")
        print(f"❌ Failed to get archive: {e}")
    
    finally:
        # Cleanup connections to prevent hanging
        if remote_memory:
            try:
                # Wait for server completion and close connections
                remote_memory.wait_for_server_completion(timeout=5.0)
                remote_memory.close()
            except Exception as cleanup_e:
                logger.debug(f"Cleanup warning: {cleanup_e}")
        
        # Shutdown write queue to prevent hanging
        try:
            from serena.infrastructure.write_queue import write_queue
            shutdown_success = write_queue.shutdown(timeout=5.0)
            if shutdown_success:
                logger.debug("✅ Write queue shutdown completed")
            else:
                logger.debug("⚠️ Write queue shutdown timeout")
        except ImportError:
            # Write queue not available - normal for some configurations
            pass
        except Exception as queue_e:
            logger.debug(f"Write queue cleanup warning: {queue_e}")


def register(sub: Any) -> None:
    """Register the get command."""
    p = sub.add_parser("get", help="Get specific archive by task ID")
    p.add_argument("task_id", help="Task ID to retrieve")
    p.add_argument("--content", action="store_true", help="Show full content")
    p.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    p.set_defaults(func=cmd_get)