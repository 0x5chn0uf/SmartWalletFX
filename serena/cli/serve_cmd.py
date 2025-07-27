from __future__ import annotations

"""`serena serve` command – run HTTP server."""

import logging
from typing import Any


def cmd_serve(args) -> None:
    """Run local HTTP server exposing memory API."""
    logger = logging.getLogger(__name__)
    
    try:
        import uvicorn
        from serena.infrastructure.server import create_app
        
        app = create_app()
        
        print(f"🚀 Starting Serena server on {args.host}:{args.port}")
        print(f"📖 API docs available at http://{args.host}:{args.port}/docs")
        
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level="info"
        )
        
    except ImportError:
        logger.error("FastAPI/Uvicorn not available. Install with: pip install fastapi uvicorn")
        print("❌ Server dependencies not installed. Install with: pip install fastapi uvicorn")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        print(f"❌ Failed to start server: {e}")
        raise


def register(sub: Any) -> None:
    """Register the serve command."""
    p = sub.add_parser("serve", help="Run local HTTP server exposing memory API")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--watch", action="store_true", help="Watch for file changes")
    p.set_defaults(func=cmd_serve)