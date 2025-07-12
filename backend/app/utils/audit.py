"""Audit-event validation helper.

This utility is responsible for ensuring that runtime *audit* log payloads are
well-formed and comply with the canonical :pymod:`app.schemas.audit_log` models.
It is lightweight so that it can be imported inside the hot path of
:pyfunc:`app.utils.logging.audit` without noticeable overhead.
"""
from __future__ import annotations

import os
import warnings
from typing import Any

from app.schemas.audit_log import AuditEventBase

# ---------------------------------------------------------------------------
# Configuration – behaviour can be tuned via environment variables:
#   AUDIT_VALIDATION=[hard|warn|off]
#     hard – raises an exception on validation failure (used in tests/CI)
#     warn – emits a :pyclass:`warnings.WarningMessage` but does not raise
#     off  – skips validation entirely (fast-path for high-throughput prod)
# ---------------------------------------------------------------------------

_VALIDATION_MODE = os.getenv("AUDIT_VALIDATION", "hard").lower()


class AuditValidationError(ValueError):
    """Raised when an audit payload does not conform to the schema."""


def validate_audit_event(event: dict[str, Any]) -> None:
    """Validate *event* against :class:`~app.schemas.audit_log.AuditEventBase`.

    Behaviour is controlled by ``AUDIT_VALIDATION`` environment variable.
    """

    if _VALIDATION_MODE == "off":
        return

    try:
        AuditEventBase.model_validate(event)
    except Exception as exc:  # pragma: no cover – broad catch for pydantic errors
        if _VALIDATION_MODE == "warn":
            warnings.warn(f"Invalid audit event payload: {exc}")
        else:  # hard (default)
            raise AuditValidationError(str(exc)) from exc
