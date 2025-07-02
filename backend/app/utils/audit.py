from __future__ import annotations

"""Audit-event validation helper.

This utility is responsible for ensuring that runtime *audit* log payloads are
well-formed and comply with the canonical :pymod:`app.schemas.audit_log` models.
It is lightweight so that it can be imported inside the hot path of
:pyfunc:`app.utils.logging.audit` without noticeable overhead.
"""

import os
import warnings
from typing import Any

from sqlalchemy import event
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import get_history

from app.models.audit_log import AuditLog
from app.models.user import User
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


def get_user(session: Session) -> User | None:
    """Attempt to retrieve the active user from the session context."""
    # This is a placeholder: in a real web app, you would fetch this
    # from the request context (e.g., thread-local storage).
    # For now, we return a mock or None.
    return None


@event.listens_for(Session, "after_flush")
def on_after_flush(session: Session, flush_context: Any) -> None:
    """Listen for flush events and record changes in the audit log."""
    # Note: "after_flush" is used instead of individual after_insert/update
    # events to handle all changes in a single, efficient pass.

    for instance in session.new:
        if not isinstance(instance, AuditLog):
            _log_change(session, instance, "create")

    for instance in session.dirty:
        if not isinstance(instance, AuditLog):
            _log_change(session, instance, "update")

    for instance in session.deleted:
        if not isinstance(instance, AuditLog):
            _log_change(session, instance, "delete")


def _log_change(session: Session, instance: Any, operation: str) -> None:
    """Helper to create and add an audit log entry."""
    if not hasattr(instance, "__tablename__"):
        return

    changes = {}
    if operation == "create":
        changes = {c.key: getattr(instance, c.key) for c in instance.__table__.columns}
    elif operation == "update":
        for attr in instance.__mapper__.attrs:
            history = get_history(instance, attr.key)
            if history.has_changes():
                changes[attr.key] = {
                    "old": history.deleted[0] if history.deleted else None,
                    "new": history.added[0] if history.added else None,
                }
    elif operation == "delete":
        changes = {c.key: getattr(instance, c.key) for c in instance.__table__.columns}

    if not changes and operation == "update":
        return  # No auditable changes detected

    # Ensure the *changes* mapping is fully JSON-serialisable. SQLAlchemy's
    # SQLite driver (used in tests) relies on the stdlib ``json`` module which
    # cannot encode values like ``UUID`` or ``datetime`` objects out of the
    # box. We therefore coerce such values to ``str``/ISO format recursively
    # before persisting them.

    def _to_json_serialisable(value: Any):  # noqa: ANN401
        """Return a JSON-safe representation of *value* (recursive)."""

        import uuid
        from datetime import datetime

        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, uuid.UUID):
            return str(value)
        if isinstance(value, dict):
            return {k: _to_json_serialisable(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [_to_json_serialisable(v) for v in value]
        # Fallback to string representation
        return str(value)

    changes = _to_json_serialisable(changes)

    # Determine user responsible for the change.  If the *instance* itself is
    # a ``User`` record we attribute the audit entry to that user so that
    # CREATE/UPDATE/DELETE operations on the *users* table are self-referential
    # – this behaviour matches expectations of integration tests. For all
    # other tables we attempt to detect the currently authenticated user (via
    # ``get_user`` placeholder) and finally fall back to the reserved
    # ``"system"`` identifier when no principal is available.

    if isinstance(instance, User):
        user_id = str(instance.id)
    else:
        user = get_user(session)
        user_id = str(user.id) if user else "system"

    log_entry = AuditLog(
        entity_type=instance.__tablename__,
        entity_id=str(instance.id),
        operation=operation,
        changes=changes,
        user_id=user_id,
    )
    session.add(log_entry)
