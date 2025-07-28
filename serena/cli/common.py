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
    """Remote memory client that uses server API for operations."""
    
    def __init__(self, server_url: str = None):
        from serena import config
        self.server_url = server_url or config.server_url()
        if not self.server_url.startswith('http'):
            self.server_url = f"http://{self.server_url}"
    
    def _make_request(self, method: str, endpoint: str, **kwargs):
        """Make HTTP request to server."""
        import requests
        import logging
        
        url = f"{self.server_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            response = requests.request(method, url, timeout=30, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Request to {url} failed: {e}")
            raise RuntimeError(f"Server request failed: {e}")
    
    def search(self, query: str, limit: int = 10):
        """Search archives using server API."""
        try:
            response = self._make_request('GET', '/search', params={'q': query, 'limit': limit})
            return response.get('results', [])
        except Exception as e:
            logging.error(f"Remote search failed: {e}")
            return []
    
    def get(self, task_id: str):
        """Get archive by task ID using server API."""
        try:
            return self._make_request('GET', f'/archives/{task_id}')
        except Exception as e:
            logging.error(f"Remote get failed for {task_id}: {e}")
            return None
    
    def upsert(self, task_id: str, markdown_text: str, filepath: str = None, 
               title: str = None, kind: str = "archive", status: str = None, 
               completed_at: str = None) -> bool:
        """Upsert archive using server API."""
        try:
            data = {
                'task_id': task_id,
                'markdown_text': markdown_text,
            }
            
            if filepath:
                data['filepath'] = filepath
            if title:
                data['title'] = title
            if kind:
                data['kind'] = kind
            if status:
                data['status'] = status
            if completed_at:
                data['completed_at'] = completed_at
            
            response = self._make_request('POST', '/archives', json=data)
            return response.get('status') == 'success'
        except Exception as e:
            logging.error(f"Remote upsert failed for {task_id}: {e}")
            return False
    
    def is_server_available(self) -> bool:
        """Check if server is available."""
        try:
            self._make_request('GET', '/health')
            return True
        except Exception:
            return False


__all__ = [
    "setup_logging",
    "remote_upsert", 
    "detect_taskmaster_directories",
    "RemoteMemory",
]