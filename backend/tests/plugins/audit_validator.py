from __future__ import annotations

import json
import logging
from typing import Any

import pytest

from app.utils.audit import AuditValidationError, validate_audit_event

# ---------------------------------------------------------------------------
# Pytest *autouse* fixture – executed for every test function.  It captures
# log records emitted via the built-in *caplog* fixture, filters for the
# dedicated "audit" logger, parses the JSON payload and validates it against
# the canonical Pydantic schema via :pyfunc:`validate_audit_event`.
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _validate_audit_logs(caplog: pytest.LogCaptureFixture) -> None:  # noqa: D401
    """Automatically validate *audit* log entries after each test.

    • Sets logging level INFO for the "audit" logger so that records are
      captured even if the test didn't explicitly adjust *caplog* levels.
    • Runs *after* the test code (``yield``) to avoid interfering with the
      test's own log-assertions.
    """

    caplog.set_level(logging.INFO, logger="audit")
    yield  # Run the actual test

    for record in caplog.records:
        if record.name != "audit" or record.levelno != logging.INFO:
            continue

        try:
            payload: dict[str, Any] = json.loads(record.getMessage())
        except Exception as exc:  # pragma: no cover – malformed JSON should fail
            pytest.fail(
                f"Audit log record is not valid JSON: {exc}\n{record.getMessage()}"
            )

        try:
            validate_audit_event(payload)
        except AuditValidationError as exc:
            pytest.fail(f"Invalid audit event payload: {exc}\nPayload: {payload}")
