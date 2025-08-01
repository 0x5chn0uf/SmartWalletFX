from __future__ import annotations

"""`serena serve` command – run HTTP server."""

import logging
import signal
import sys
from typing import Any


def cmd_serve(args) -> None:
    """Run local HTTP server exposing memory API."""
    try:
        import uvicorn

        from serena.infrastructure.server import create_app

        app = create_app()

        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            print(f"Received signal {signum}, initiating shutdown")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

        print(f"🚀 Starting Serena server on {args.host}:{args.port}")
        print(f"📖 API docs available at http://{args.host}:{args.port}/docs")
        print(f"📊 Health check: http://{args.host}:{args.port}/health")

        # Configure uvicorn logging
        log_config = uvicorn.config.LOGGING_CONFIG
        log_config["formatters"]["default"][
            "fmt"
        ] = "%(asctime)s - %(levelname)s - %(message)s"

        # Set log level based on args
        log_level = "debug" if args.verbose else "info"

        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level=log_level,
            log_config=log_config,
            reload=args.watch,
            access_log=False,  # Disable default access log, use our custom middleware
        )

    except ImportError as e:
        print(
            "FastAPI/Uvicorn not available. {e}\nInstall with: pip install fastapi uvicorn"
        )
        print(
            "❌ Server dependencies not installed. Install with: pip install fastapi uvicorn"
        )
    except Exception as e:
        print(f"Failed to start server: {e}")
        print(f"❌ Failed to start server: {e}")
        raise


def register(sub: Any) -> None:
    """Register the serve command."""
    p = sub.add_parser("serve", help="Run local HTTP server exposing memory API")
    p.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    p.add_argument("--port", type=int, default=8765, help="Port to bind to")
    p.add_argument(
        "--watch", action="store_true", help="Watch for file changes and auto-reload"
    )
    p.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    p.set_defaults(func=cmd_serve)
