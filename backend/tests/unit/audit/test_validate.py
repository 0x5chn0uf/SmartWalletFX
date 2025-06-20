from __future__ import annotations

import importlib
import os

import pytest

from app.utils import audit as audit_utils


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
