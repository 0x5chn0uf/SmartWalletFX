from __future__ import annotations

"""Common helpers for Serena CLI."""

import logging
import sys
from pathlib import Path
from typing import List


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def remote_upsert(task_id: str, markdown_text: str, **meta) -> bool:
    """Remote upsert placeholder - not implemented yet."""
    logging.warning("Remote upsert not implemented in new CLI")
    return False


def detect_taskmaster_directories() -> List[str]:
    """Detect TaskMaster directories in the current project."""
    directories = []
    
    # Common TaskMaster directory patterns
    taskmaster_patterns = [
        ".taskmaster/memory-bank",
        ".taskmaster/tasks",
        ".taskmaster/archives",
        ".serena/memories",
        "docs",
    ]
    
    for pattern in taskmaster_patterns:
        path = Path(pattern)
        if path.exists() and path.is_dir():
            directories.append(str(path))
    
    return directories


class RemoteMemory:
    """Placeholder for remote memory - not implemented yet."""
    
    def __init__(self, server_url: str = ""):
        self.server_url = server_url
        logging.warning("RemoteMemory not implemented in new CLI")
    
    def search(self, query: str, limit: int = 10):
        """Search placeholder."""
        logging.warning("Remote search not implemented")
        return []
    
    def get(self, task_id: str):
        """Get placeholder."""
        logging.warning("Remote get not implemented")
        return None


__all__ = [
    "setup_logging",
    "remote_upsert", 
    "detect_taskmaster_directories",
    "RemoteMemory",
]