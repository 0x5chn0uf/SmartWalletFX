"""Project-wide structured logging configuration using *structlog*.

Call :func:`setup_logging` once during application startup **before** other
modules log to ensure processor pipeline is configured.
"""

from __future__ import annotations

import logging

import structlog


def _configure_structlog() -> None:
    """Configure structlog to emit JSON records with contextvars support."""

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            timestamper,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )


def setup_logging() -> None:  # pragma: no cover – one-time bootstrapping
    """Initialise the stdlib & structlog configuration."""

    # Basic stdlib config (structlog will re-use root handlers)
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )

    _configure_structlog()

    # Silence noisy dependencies to *WARNING* level
    for noisy in [
        "sqlalchemy.engine",
        "uvicorn.error",
        "uvicorn.access",
    ]:
        logging.getLogger(noisy).setLevel(logging.WARNING)


# Convenience global import – avoids reconfiguring in sub-processes
setup_logging()
