from __future__ import annotations

import importlib

import pytest

from app.utils import audit as audit_utils


@pytest.mark.unit
def test_validate_audit_event_accepts_valid(monkeypatch):
    monkeypatch.setenv("AUDIT_VALIDATION", "hard")
    importlib.reload(audit_utils)  # reload to apply env var

    event = {
        "timestamp": "2025-06-20T12:00:00Z",
        "action": "user_login",
        "result": "success",
    }

    # Should not raise
    audit_utils.validate_audit_event(event)


@pytest.mark.unit
def test_validate_audit_event_rejects_invalid(monkeypatch):
    monkeypatch.setenv("AUDIT_VALIDATION", "hard")
    importlib.reload(audit_utils)

    # Missing required 'timestamp'
    event = {
        "action": "user_login",
        "result": "success",
    }
    with pytest.raises(audit_utils.AuditValidationError):
        audit_utils.validate_audit_event(event)


@pytest.mark.unit
def test_validate_audit_event_warn_mode(monkeypatch):
    monkeypatch.setenv("AUDIT_VALIDATION", "warn")
    importlib.reload(audit_utils)

    # Invalid event should only warn, not raise
    event = {
        "action": "user_login",  # Missing timestamp
        "result": "success",
    }
    with pytest.warns(UserWarning):
        audit_utils.validate_audit_event(event)


@pytest.mark.unit
def test_validate_audit_event_off_mode(monkeypatch):
    monkeypatch.setenv("AUDIT_VALIDATION", "off")
    importlib.reload(audit_utils)

    # Invalid event should not raise or warn
    event = {
        "action": "user_login",  # Missing timestamp
        "result": "success",
    }
    audit_utils.validate_audit_event(event)  # Should not raise or warn
