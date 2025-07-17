"""Logging service for application-wide logging configuration and management."""

from __future__ import annotations

import logging
import sys

import structlog

from app.core.config import ConfigurationService


class CoreLogging:
    """Service for managing application logging configuration."""

    def __init__(self, config_service: ConfigurationService):
        """Initialize logging service with configuration."""
        self.config_service = config_service
        self._is_setup = False

    def setup_logging(self) -> None:
        """Set up structured logging configuration."""
        if self._is_setup:
            return  # Avoid duplicate setup

        # Get log level from config
        log_level_str = self.config_service.LOG_LEVEL
        log_level = getattr(logging, log_level_str, logging.INFO)

        # Basic stdlib config (structlog will re-use root handlers)
        root_logger = logging.getLogger()
        if not root_logger.hasHandlers():
            logging.basicConfig(
                level=log_level,
                format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
                stream=sys.stdout,
            )
        else:
            # If handlers already exist, just set the level and formatter
            for handler in root_logger.handlers:
                handler.setLevel(log_level)
                handler.setFormatter(
                    logging.Formatter(
                        "%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"
                    )
                )

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
            wrapper_class=structlog.make_filtering_bound_logger(min_level=log_level),
            cache_logger_on_first_use=True,
        )

        # Silence noisy dependencies to *WARNING* level
        for noisy in [
            "sqlalchemy.engine",
            "uvicorn.error",
            "uvicorn.access",
        ]:
            logging.getLogger(noisy).setLevel(logging.WARNING)
        self._is_setup = True

    def get_logger(self, name: str) -> structlog.BoundLogger:
        """Get a structured logger instance."""
        if not self._is_setup:
            self.setup_logging()
        return structlog.get_logger(name)

    def is_setup(self) -> bool:
        """Check if logging has been set up."""
        return self._is_setup
