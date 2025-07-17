"""Unit tests covering app.utils.logging.audit helper."""

from __future__ import annotations

import json
import logging
import sys
import types
from datetime import datetime, timezone
from io import StringIO
from unittest.mock import Mock, patch

import pytest
from structlog.contextvars import bind_contextvars, clear_contextvars

from app.domain.schemas.audit_log import AuditEventBase
from app.utils import logging as audit_logging
from app.utils.audit import AuditValidationError
from app.utils.logging import Audit


def test_audit_logging_includes_trace_id(monkeypatch):
    """Ensure audit() attaches trace_id from structlog contextvars when present."""

    fake_ctx_module = types.SimpleNamespace(get_contextvars=lambda: {"trace_id": "abc"})
    monkeypatch.setitem(sys.modules, "structlog.contextvars", fake_ctx_module)

    stream = StringIO()
    handler = logging.StreamHandler(stream)
    audit_logger = audit_logging._AUDIT_LOGGER  # pylint: disable=protected-access
    audit_logger.addHandler(handler)

    audit_logging.Audit.info("unit_test", foo=1)

    audit_logger.removeHandler(handler)
    handler.flush()

    log_json = json.loads(stream.getvalue())
    assert log_json["action"] == "unit_test"
    assert log_json["trace_id"] == "abc"
    assert log_json["foo"] == 1


class TestStructuredAuditLogging:
    def test_log_structured_audit_event_basic(self, caplog):
        """Test basic structured audit logging."""
        # Capture logs from the dedicated "audit" logger directly
        caplog.set_level(logging.INFO, logger="audit")

        event = AuditEventBase(
            id="123", timestamp=datetime.now(timezone.utc), action="test_event"
        )
        audit_logger = logging.getLogger("audit")
        audit_logger.addHandler(
            caplog.handler
        )  # ensure records captured despite propagate=False

        try:
            Audit.log_structured_audit_event(event)

            # Ensure at least one audit log was emitted
            assert (
                caplog.records
            ), "Expected at least one audit log record to be captured from 'audit' logger"
            record = caplog.records[-1]
            assert record.levelname == "INFO"
            assert record.name == "audit"

            # Verify JSON structure
            payload = json.loads(record.message)
            assert payload["id"] == "123"
            assert payload["action"] == "test_event"
            assert "timestamp" in payload
        finally:
            audit_logger.removeHandler(caplog.handler)

    def test_log_structured_audit_event_with_trace_id(self, caplog):
        """Test structured audit logging with trace ID from context."""
        caplog.set_level(logging.INFO, logger="audit")

        # Set up trace ID in context
        bind_contextvars(trace_id="test-trace-123")

        audit_logger = logging.getLogger("audit")
        audit_logger.addHandler(caplog.handler)

        try:
            event = AuditEventBase(
                id="123", timestamp=datetime.now(timezone.utc), action="test_event"
            )

            Audit.log_structured_audit_event(event)

            assert caplog.records, "Expected audit log record"
            payload = json.loads(caplog.records[-1].message)
            assert payload["trace_id"] == "test-trace-123"
        finally:
            clear_contextvars()
            audit_logger.removeHandler(caplog.handler)

    def test_log_structured_audit_event_validation_failure(self, caplog):
        """Test handling of validation failures in structured audit logging."""
        caplog.set_level(logging.INFO, logger="audit")

        # Create an invalid event (missing required fields)
        with pytest.raises(Exception):
            # This should fail validation during model creation
            AuditEventBase(
                id="123",
                timestamp=None,  # type: ignore # This will cause validation to fail
                action="",  # This will cause validation to fail
            )


class TestAuditLogging:
    def test_audit_basic(self, caplog):
        """Test basic audit logging."""
        caplog.set_level(logging.INFO, logger="audit")

        audit_logger = logging.getLogger("audit")
        audit_logger.addHandler(caplog.handler)

        try:
            Audit.info("user_action", user_id="123", action_type="login")

            assert len(caplog.records) == 1
            record = caplog.records[0]
            assert record.levelname == "INFO"
            assert record.name == "audit"

            # Verify JSON structure (ID and timestamp are not included in the
            # printable payload by design)
            payload = json.loads(record.message)
            assert payload["action"] == "user_action"
            assert payload["user_id"] == "123"
            assert payload["action_type"] == "login"
            # No "id" or "timestamp" keys expected in logged JSON

        finally:
            audit_logger.removeHandler(caplog.handler)

    def test_audit_with_trace_id(self, caplog):
        """Test audit logging with trace ID from context."""
        caplog.set_level(logging.INFO, logger="audit")

        # Set up trace ID in context
        bind_contextvars(trace_id="test-trace-123")

        audit_logger = logging.getLogger("audit")
        audit_logger.addHandler(caplog.handler)

        try:
            Audit.info("test_event")

            assert len(caplog.records) == 1
            payload = json.loads(caplog.records[0].message)
            assert payload["trace_id"] == "test-trace-123"
        finally:
            clear_contextvars()
            audit_logger.removeHandler(caplog.handler)

    def test_audit_with_validation_failure(self, caplog, monkeypatch):
        """Test handling of validation failures in audit logging."""
        caplog.set_level(logging.INFO, logger="audit")

        mock_validate = Mock(side_effect=AuditValidationError("Test validation error"))
        monkeypatch.setattr("app.utils.logging.validate_audit_event", mock_validate)

        # Create an event that will fail validation
        with pytest.raises(AuditValidationError):
            Audit.info("test_event")

    @patch("structlog.contextvars.get_contextvars")
    def test_audit_with_context_error(self, mock_get_contextvars, caplog):
        """Test audit logging when context access fails."""
        caplog.set_level(logging.INFO, logger="audit")
        mock_get_contextvars.side_effect = Exception("Context error")

        audit_logger = logging.getLogger("audit")
        audit_logger.addHandler(caplog.handler)

        try:
            # Should still log without trace ID
            Audit.info("test_event")

            assert len(caplog.records) == 1
            payload = json.loads(caplog.records[0].message)
            assert "trace_id" not in payload
        finally:
            audit_logger.removeHandler(caplog.handler)
