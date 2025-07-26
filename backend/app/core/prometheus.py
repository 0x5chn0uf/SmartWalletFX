"""Prometheus metrics configuration and registry management.

This module provides centralized Prometheus metrics setup for the application,
including the metrics registry and endpoint configuration.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prometheus client setup with graceful degradation
# ---------------------------------------------------------------------------

try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
        generate_latest,
    )
    from prometheus_client.exposition import start_http_server

    _REGISTRY = CollectorRegistry()
    _PROMETHEUS_AVAILABLE = True

except ImportError:  # pragma: no cover
    _REGISTRY = None
    _PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_client not available - metrics will be disabled")


def get_registry() -> Optional[CollectorRegistry]:
    """Get the Prometheus metrics registry.

    Returns:
        The CollectorRegistry instance if prometheus_client is available,
        None otherwise.
    """
    return _REGISTRY if _PROMETHEUS_AVAILABLE else None


def is_available() -> bool:
    """Check if Prometheus client is available.

    Returns:
        True if prometheus_client is installed and available.
    """
    return _PROMETHEUS_AVAILABLE


def generate_metrics() -> tuple[bytes, str]:
    """Generate Prometheus metrics output.

    Returns:
        Tuple of (metrics_data, content_type) for HTTP response.

    Raises:
        RuntimeError: If prometheus_client is not available.
    """
    if not _PROMETHEUS_AVAILABLE:
        raise RuntimeError("Prometheus client not available")

    return generate_latest(_REGISTRY), CONTENT_TYPE_LATEST


def start_metrics_server(port: int = 8000, addr: str = "0.0.0.0"):  # nosec B104
    """Start the Prometheus metrics HTTP server.

    Args:
        port: Port to bind the metrics server to.
        addr: Address to bind the metrics server to.

    Raises:
        RuntimeError: If prometheus_client is not available.
    """
    if not _PROMETHEUS_AVAILABLE:
        raise RuntimeError("Prometheus client not available")

    start_http_server(port, addr, registry=_REGISTRY)
    logger.info("Prometheus metrics server started on %s:%d", addr, port)
