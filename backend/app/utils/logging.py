from __future__ import annotations

"""Structured audit logging utility.

Provides a simple helper to emit JSON-serialised audit events to standard
output so that external log processors (e.g. Loki, Datadog) can parse them
reliably.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

from app.schemas.audit_log import AuditEventBase
from app.utils.audit import validate_audit_event

_AUDIT_LOGGER = logging.getLogger("audit")
if not _AUDIT_LOGGER.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter("%(message)s"))
    _AUDIT_LOGGER.addHandler(_handler)
    _AUDIT_LOGGER.setLevel(logging.INFO)


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
        from structlog.contextvars import get_context

        ctx = get_context()
        if ctx and "trace_id" in ctx and not payload.get("trace_id"):
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


def audit(event: str, **extra: Any) -> None:
    """Emit an *audit* log entry.

    Args:
        event: Event name, e.g. ``user_login_success``.
        **extra: Arbitrary key/value metadata to include in the log record.
    """

    payload: Dict[str, Any] = {
        "id": uuid4().hex,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": event,
        **extra,
    }
    try:
        from structlog.contextvars import get_context

        ctx = get_context()
        if ctx and "trace_id" in ctx:
            payload["trace_id"] = ctx["trace_id"]
    except Exception:  # pragma: no cover – structlog may not be configured
        pass
    _AUDIT_LOGGER.info(json.dumps(payload, separators=(",", ":")))

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
