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
from app.utils.audit import validate_audit_event

_AUDIT_LOGGER = logging.getLogger("audit")

# ---------------------------------------------------------------------------
# Fancy coloured output helper
# ---------------------------------------------------------------------------


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


# Attach handler only once (avoids duplicate logs under Uvicorn workers)
if not _AUDIT_LOGGER.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(_ColoredAuditFormatter())
    _AUDIT_LOGGER.addHandler(_handler)
    _AUDIT_LOGGER.setLevel(logging.INFO)
    # Prevent double logging via root handlers
    _AUDIT_LOGGER.propagate = False


def _json_safe(obj):
    """Recursively convert UUID and datetime objects
    in a dict/list to strings for JSON serialization."""
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    elif isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj


def log_structured_audit_event(event: AuditEventBase) -> None:
    """Emit a structured audit log from a Pydantic model.

    Args:
        event: A Pydantic model instance inheriting from AuditEventBase.
    """
    # by_alias=True ensures model fields with aliases (like sha256) are
    # serialised with their alias name.
    payload = event.model_dump(by_alias=True)

    # Add trace_id from context if available and not already set
    try:
        from structlog.contextvars import get_contextvars

        ctx = get_contextvars()
        if ctx and "trace_id" in ctx and payload.get("trace_id") is None:
            payload["trace_id"] = ctx["trace_id"]
    except Exception:  # pragma: no cover
        pass

    _AUDIT_LOGGER.info(json.dumps(payload, default=str, separators=(",", ":")))

    # Validation is implicitly handled by Pydantic model creation before this
    # function is called, but we run the validator anyway to respect the
    # AUDIT_VALIDATION=[hard|warn|off] modes.
    try:
        validate_audit_event(payload)
    except Exception:
        # Re-raise to surface errors in *hard* mode; in *warn/off* the helper
        # already handled warning emission or silent discard.
        raise


def audit(event: str, *, level: str = "INFO", **extra: Any) -> None:
    """Emit an *audit* log entry.

    Args:
        event: Event name, e.g. ``user_login_success``.
        level: Logging level – one of "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL".
        **extra: Arbitrary key/value metadata to include in the log record.
    """

    # Determine call-site (module path + function) if *route* not provided.
    route = None
    try:
        current_file = __file__.replace("\\", "/")
        stack = inspect.stack()[1:]
        for frame_info in stack:
            path = frame_info.filename.replace("\\", "/")
            # Skip internal helper frames (this module)
            if path == current_file:
                continue
            # Build relative path starting at app/
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

    # Prepare visual representation without noisy meta fields
    printable = payload.copy()
    printable.pop("id", None)
    printable.pop("timestamp", None)

    log_method = getattr(_AUDIT_LOGGER, level.lower(), _AUDIT_LOGGER.info)
    log_method(
        json.dumps(_json_safe(printable), separators=(",", ":")),
        extra={"route": route} if route else None,
    )

    # ------------------------------------------------------------------
    # Validate payload (optional hard/warn/off behaviour is configured via
    # AUDIT_VALIDATION environment variable).  This runs *after* the log is
    # emitted to avoid blocking critical-path execution in production – but
    # still fails the test-suite early when running in *hard* mode.
    # ------------------------------------------------------------------
    try:
        validate_audit_event(payload)
    except Exception:
        # Re-raise to surface errors in *hard* mode; in *warn/off* the helper
        # already handled warning emission or silent discard.
        raise


# ---------------------------------------------------------------------------
# Public convenience wrapper – enables Audit.info(...), Audit.error(...), …
# ---------------------------------------------------------------------------


class Audit:  # noqa: D101 – thin convenience facade
    @staticmethod
    def info(event: str, **extra: Any) -> None:  # noqa: D401
        audit(event, level="INFO", **extra)

    @staticmethod
    def debug(event: str, **extra: Any) -> None:  # noqa: D401
        audit(event, level="DEBUG", **extra)

    @staticmethod
    def warning(event: str, **extra: Any) -> None:  # noqa: D401
        audit(event, level="WARNING", **extra)

    @staticmethod
    def error(event: str, **extra: Any) -> None:  # noqa: D401
        audit(event, level="ERROR", **extra)

    @staticmethod
    def critical(event: str, **extra: Any) -> None:  # noqa: D401
        audit(event, level="CRITICAL", **extra)
