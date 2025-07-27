from __future__ import annotations

"""`serena init` command."""

import logging
from typing import Any

from serena.infrastructure.database import init_database


def cmd_init(args) -> None:
    """Initialize Serena database and configuration."""
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize the database
        init_database()
        logger.info("Serena database initialized successfully")
        
        # TODO: Add configuration file creation if needed
        # TODO: Add auto-detection of project structure
        
        print("✅ Serena initialized successfully!")
        
    except Exception as e:
        logger.error(f"Failed to initialize Serena: {e}")
        print(f"❌ Initialization failed: {e}")
        raise


def register(sub: Any) -> None:  # sub is argparse subparser
    """Register the init command."""
    parser = sub.add_parser("init", help="Initialize Serena (DB, config, auto-detect)")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.set_defaults(func=cmd_init)