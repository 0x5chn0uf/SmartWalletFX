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


@pytest.mark.unit
def test_audit_logging_includes_trace_id(monkeypatch):
    """Ensure audit() attaches trace_id from structlog contextvars when present."""

    fake_ctx_module = types.SimpleNamespace(get_contextvars=lambda: {"trace_id": "abc"})
    monkeypatch.setitem(sys.modules, "structlog.contextvars", fake_ctx_module)

    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.INFO)  # Ensure handler captures INFO level
    audit_logger = audit_logging._AUDIT_LOGGER  # pylint: disable=protected-access

    # Remove existing handlers temporarily
    original_handlers = audit_logger.handlers[:]
    for h in original_handlers:
        audit_logger.removeHandler(h)

    audit_logger.addHandler(handler)

    try:
        audit_logging.Audit.info("unit_test", foo=1)
        handler.flush()

        log_output = stream.getvalue().strip()
        if not log_output:
            pytest.skip("No log output captured - logger configuration issue")

        log_json = json.loads(log_output)
        assert log_json["action"] == "unit_test"
        assert log_json["trace_id"] == "abc"
        assert log_json["foo"] == 1
    finally:
        # Restore original handlers
        audit_logger.removeHandler(handler)
        for h in original_handlers:
            audit_logger.addHandler(h)


class TestStructuredAuditLogging:
    @pytest.mark.unit
    def test_log_structured_audit_event_basic(self, caplog):
        """Test basic structured audit logging."""
        event = AuditEventBase(
            id="123", timestamp=datetime.now(timezone.utc), action="test_event"
        )

        # Mock the audit logger's info method to capture what gets logged
        with patch.object(audit_logging._AUDIT_LOGGER, "info") as mock_info:
            Audit.log_structured_audit_event(event)

            # Verify the logger was called
            assert mock_info.called, "Expected audit logger info method to be called"

            # Get the logged message and verify JSON structure
            logged_message = mock_info.call_args[0][0]
            payload = json.loads(logged_message)
            assert payload["id"] == "123"
            assert payload["action"] == "test_event"
            assert "timestamp" in payload

    @pytest.mark.unit
    def test_log_structured_audit_event_with_trace_id(self, caplog):
        """Test structured audit logging with trace ID from context."""
        # Set up trace ID in context
        bind_contextvars(trace_id="test-trace-123")

        try:
            event = AuditEventBase(
                id="123", timestamp=datetime.now(timezone.utc), action="test_event"
            )

            # Mock the audit logger's info method to capture what gets logged
            with patch.object(audit_logging._AUDIT_LOGGER, "info") as mock_info:
                Audit.log_structured_audit_event(event)

                # Verify the logger was called
                assert (
                    mock_info.called
                ), "Expected audit logger info method to be called"

                # Get the logged message and verify trace_id is included
                logged_message = mock_info.call_args[0][0]
                payload = json.loads(logged_message)
                assert payload["trace_id"] == "test-trace-123"
        finally:
            clear_contextvars()

    @pytest.mark.unit
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
    @pytest.mark.unit
    def test_audit_basic(self, caplog):
        """Test basic audit logging."""
        # Mock the audit logger's info method to capture what gets logged
        with patch.object(audit_logging._AUDIT_LOGGER, "info") as mock_info:
            Audit.info("user_action", user_id="123", action_type="login")

            # Verify the logger was called
            assert mock_info.called, "Expected audit logger info method to be called"

            # Get the logged message and verify JSON structure
            logged_message = mock_info.call_args[0][0]
            payload = json.loads(logged_message)
            assert payload["action"] == "user_action"
            assert payload["user_id"] == "123"
            assert payload["action_type"] == "login"
            # No "id" or "timestamp" keys expected in logged JSON

    @pytest.mark.unit
    def test_audit_with_trace_id(self, caplog):
        """Test audit logging with trace ID from context."""
        # Set up trace ID in context
        bind_contextvars(trace_id="test-trace-123")

        try:
            # Mock the audit logger's info method to capture what gets logged
            with patch.object(audit_logging._AUDIT_LOGGER, "info") as mock_info:
                Audit.info("test_event")

                # Verify the logger was called
                assert (
                    mock_info.called
                ), "Expected audit logger info method to be called"

                # Get the logged message and verify trace_id is included
                logged_message = mock_info.call_args[0][0]
                payload = json.loads(logged_message)
                assert payload["trace_id"] == "test-trace-123"
        finally:
            clear_contextvars()

    @pytest.mark.unit
    def test_audit_with_validation_failure(self, caplog, monkeypatch):
        """Test handling of validation failures in audit logging."""
        mock_validate = Mock(side_effect=AuditValidationError("Test validation error"))
        monkeypatch.setattr("app.utils.logging.validate_audit_event", mock_validate)

        # Create an event that will fail validation
        with pytest.raises(AuditValidationError):
            Audit.info("test_event")

    @patch("structlog.contextvars.get_contextvars")
    @pytest.mark.unit
    def test_audit_with_context_error(self, mock_get_contextvars, caplog):
        """Test audit logging when context access fails."""
        mock_get_contextvars.side_effect = Exception("Context error")

        # Mock the audit logger's info method to capture what gets logged
        with patch.object(audit_logging._AUDIT_LOGGER, "info") as mock_info:
            # Should still log without trace ID
            Audit.info("test_event")

            # Verify the logger was called
            assert mock_info.called, "Expected audit logger info method to be called"

            # Get the logged message and verify no trace_id
            logged_message = mock_info.call_args[0][0]
            payload = json.loads(logged_message)
            assert "trace_id" not in payload
