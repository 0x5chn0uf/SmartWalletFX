from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

# -------------- Audit Log Schemas --------------------------------------------
# NOTE: This file is intentionally self-contained and free of FastAPI/ORM imports
# so that it can be re-used by CLI utilities and log-parsers without pulling in
# the full application stack.


class AuditEventBase(BaseModel):
    """Base schema for every structured *audit* log event.

    The schema is intentionally permissive (extra fields are allowed) to enable
    gradual evolution.  Concrete event types should *extend* this model and add
    the required field set for their category.
    """

    id: str = Field(
        default_factory=lambda: uuid4().hex,
        description="Unique identifier for the audit event",
    )
    timestamp: datetime = Field(
        ...,
        description="Event timestamp in UTC ISO format",
    )
    action: str = Field(
        ...,
        description="Event name e.g. `user_login_success`",
    )
    trace_id: Optional[str] = Field(
        default=None, description="Correlation ID attached to the request scope"
    )

    # Allow service-specific metadata fields without schema changes
    model_config = {
        "extra": "allow",
        "populate_by_name": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "fc0b5e5cf2a140208210b8e2bc4f0711",
                    "timestamp": "2025-06-20T12:00:00Z",
                    "action": "user_login_success",
                    "trace_id": "abc123",
                    "user_id": "42",
                    "ip_address": "203.0.113.1",
                }
            ]
        },
    }

    # --- Validators ---------------------------------------------------------

    @field_validator("timestamp", mode="before")
    @classmethod
    def _parse_ts(cls, v: str | datetime) -> datetime:  # noqa: D401
        """Ensure *timestamp* is parsed as *aware* datetime."""

        if isinstance(v, datetime):
            return v
        return datetime.fromisoformat(v.replace("Z", "+00:00"))


class AuthEvent(AuditEventBase):
    """Audit event emitted by authentication & authorisation subsystems."""

    user_id: Optional[str] = Field(None, description="Authenticated user id")
    ip_address: Optional[str] = Field(None, description="Source IPv4/6 address")
    user_agent: Optional[str] = Field(None, description="HTTP User-Agent header")
    result: str = Field(..., description="`success` | `failure` | `locked_out`")

    model_config = {"extra": "allow"}


# ---------------------------------------------------------------------------
# Helper util – JSON Schema export (used by docs / SIEM pipelines)
# ---------------------------------------------------------------------------


def audit_json_schema() -> Dict[str, Any]:
    """Return the JSON schema for the *base* audit event.

    Concrete event classes purposely inherit from *AuditEventBase*; consumers
    that only need a *generic* schema may rely on this helper.
    """

    return AuditEventBase.model_json_schema()
