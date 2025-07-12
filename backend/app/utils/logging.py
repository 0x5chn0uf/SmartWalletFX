"""Structured audit logging utility.

Provides a simple helper to emit JSON-serialised audit events to standard
output so that external log processors (e.g. Loki, Datadog) can parse them
reliably.
"""
from __future__ import annotations

import inspect
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4


from app.schemas.audit_log import AuditEventBase


def validate_audit_event(event: dict[str, Any]) -> None:
    """Delegate to :func:`app.utils.audit.validate_audit_event` lazily."""

    from app.utils.audit import validate_audit_event as _validate

    _validate(event)



class _ColoredAuditFormatter(logging.Formatter):
    """Custom formatter that prints `[LEVEL] (Route: /path): {json}`.

    Colours are enabled when running in a TTY or when `LOG_COLOR=1` env-var is
    set.  Disable by exporting `LOG_COLOR=0`.
    """

    # Basic ANSI colours – fallbacks are safe even when colour is disabled
    _LEVEL_COLOURS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    _ROUTE_COLOUR = "\033[34m"  # Blue
    _RESET = "\033[0m"

    def __init__(self, *args, **kwargs):  # noqa: D401 – passthrough
        super().__init__(*args, **kwargs)
        self._enable_colour: bool = self._detect_colour()

    def _detect_colour(self) -> bool:
        """Return ``True`` if ANSI colours should be enabled."""

        if os.getenv("LOG_COLOR") is not None:
            return os.getenv("LOG_COLOR", "1").lower() not in {"0", "false"}
        return sys.stdout.isatty()

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401 – override
        level = record.levelname
        colour_prefix = (
            self._LEVEL_COLOURS.get(level, "") if self._enable_colour else ""
        )
        reset = self._RESET if self._enable_colour else ""

        level_part = f"{colour_prefix}[{level}]{reset}"

        route: Optional[str] = getattr(record, "route", None)
        route_part = ""
        if route:
            route_colour = self._ROUTE_COLOUR if self._enable_colour else ""
            route_part = f" {route_colour}(Route: {route}){reset}"

        return f"{level_part}{route_part}: {record.getMessage()}"


class LoggingService:
    """Manage audit logging configuration and helpers."""

    def __init__(self, *, logger_name: str = "audit") -> None:
        self._logger = logging.getLogger(logger_name)
        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(_ColoredAuditFormatter())
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.INFO)
            self._logger.propagate = False

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    @staticmethod
    def _json_safe(obj):
        """Recursively convert UUID and datetime objects in ``obj`` to strings."""

        if isinstance(obj, dict):
            return {k: LoggingService._json_safe(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [LoggingService._json_safe(v) for v in obj]
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        try:
            json.dumps(obj)  # type: ignore[arg-type]
            return obj
        except TypeError:
            return str(obj)

    # ------------------------------------------------------------------
    # Structured audit logging
    # ------------------------------------------------------------------
    def log_structured_audit_event(self, event: AuditEventBase) -> None:
        """Emit a structured audit log from a Pydantic model."""

        payload = event.model_dump(by_alias=True)

        try:
            from structlog.contextvars import get_contextvars

            ctx = get_contextvars()
            if ctx and "trace_id" in ctx and payload.get("trace_id") is None:
                payload["trace_id"] = ctx["trace_id"]
        except Exception:  # pragma: no cover
            pass

        self._logger.info(
            json.dumps(payload, default=str, separators=(",", ":"))
        )

        try:
            validate_audit_event(payload)
        except Exception:
            raise

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    def audit(self, event: str, *, level: str = "INFO", **extra: Any) -> None:
        """Emit an audit log entry."""

        route = None
        try:
            current_file = __file__.replace("\\", "/")
            stack = inspect.stack()[1:]
            for frame_info in stack:
                path = frame_info.filename.replace("\\", "/")
                if path == current_file:
                    continue
                app_idx = path.rfind("app/")
                rel_path = path[app_idx:] if app_idx != -1 else path
                route = f"{rel_path}:{frame_info.function}"
                break
        except Exception:  # pragma: no cover
            pass

        payload: Dict[str, Any] = {
            "id": uuid4().hex,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": event,
            **extra,
        }
        try:
            from structlog.contextvars import get_contextvars

            ctx = get_contextvars()
            if ctx and "trace_id" in ctx:
                payload["trace_id"] = ctx["trace_id"]
        except Exception:  # pragma: no cover – structlog may not be configured
            pass

        printable = payload.copy()
        printable.pop("id", None)
        printable.pop("timestamp", None)

        log_method = getattr(self._logger, level.lower(), self._logger.info)
        log_method(
            json.dumps(LoggingService._json_safe(printable), separators=(",", ":")),
            extra={"route": route} if route else None,
        )

        try:
            validate_audit_event(payload)
        except Exception:
            raise

    def info(self, message: str, **extra: Any) -> None:  # noqa: D401
        self.audit(message, level="INFO", **extra)

    def debug(self, message: str, **extra: Any) -> None:  # noqa: D401
        self.audit(message, level="DEBUG", **extra)

    def warning(self, message: str, **extra: Any) -> None:  # noqa: D401
        self.audit(message, level="WARNING", **extra)

    def error(self, message: str, **extra: Any) -> None:  # noqa: D401
        self.audit(message, level="ERROR", **extra)

    def critical(self, message: str, **extra: Any) -> None:  # noqa: D401
        self.audit(message, level="CRITICAL", **extra)


# Default logging service and backwards compatibility helpers ------------
logging_service = LoggingService()
_AUDIT_LOGGER = logging_service._logger


class Audit:  # noqa: D101 – thin convenience facade
    @staticmethod
    def log_structured_audit_event(event: AuditEventBase) -> None:
        logging_service.log_structured_audit_event(event)

    @staticmethod
    def audit(event: str, *, level: str = "INFO", **extra: Any) -> None:
        logging_service.audit(event, level=level, **extra)

    @staticmethod
    def info(message: str, **extra: Any) -> None:  # noqa: D401
        logging_service.info(message, **extra)

    @staticmethod
    def debug(message: str, **extra: Any) -> None:  # noqa: D401
        logging_service.debug(message, **extra)

    @staticmethod
    def warning(message: str, **extra: Any) -> None:  # noqa: D401
        logging_service.warning(message, **extra)

    @staticmethod
    def error(message: str, **extra: Any) -> None:  # noqa: D401
        logging_service.error(message, **extra)

    @staticmethod
    def critical(message: str, **extra: Any) -> None:  # noqa: D401
        logging_service.critical(message, **extra)

