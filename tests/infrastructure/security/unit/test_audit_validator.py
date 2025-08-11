import warnings
from datetime import datetime

import pytest

import app.validators.audit_validator as audit_validator
from app.validators.audit_validator import (
    AuditValidationError,
    validate_audit_event,
)

# Minimal valid event for AuditEventBase
VALID_EVENT = {
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "action": "user_login_success",
}

INVALID_EVENT = {
    # missing required 'action' and 'timestamp' fields
    "foo": "bar"
}


@pytest.mark.unit
def test_validate_audit_event_hard_mode_valid():
    audit_validator._VALIDATION_MODE = "hard"
    validate_audit_event(VALID_EVENT)


@pytest.mark.unit
def test_validate_audit_event_hard_mode_invalid():
    audit_validator._VALIDATION_MODE = "hard"
    with pytest.raises(AuditValidationError):
        validate_audit_event(INVALID_EVENT)


@pytest.mark.unit
def test_validate_audit_event_warn_mode_valid():
    audit_validator._VALIDATION_MODE = "warn"
    validate_audit_event(VALID_EVENT)


@pytest.mark.unit
def test_validate_audit_event_warn_mode_invalid():
    audit_validator._VALIDATION_MODE = "warn"
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        validate_audit_event(INVALID_EVENT)
        assert any("Invalid audit event payload" in str(warn.message) for warn in w)


@pytest.mark.unit
def test_validate_audit_event_off_mode_valid():
    audit_validator._VALIDATION_MODE = "off"
    validate_audit_event(VALID_EVENT)
    validate_audit_event(INVALID_EVENT)


@pytest.mark.unit
def test_validate_audit_event_default_mode(monkeypatch):
    # Unset env var, reload module, should default to 'hard'
    monkeypatch.delenv("AUDIT_VALIDATION", raising=False)
    import importlib

    import app.validators.audit_validator as av_reload

    importlib.reload(av_reload)
    # Valid event: no error
    av_reload.validate_audit_event(VALID_EVENT)
    # Invalid event: should raise
    with pytest.raises(av_reload.AuditValidationError):
        av_reload.validate_audit_event(INVALID_EVENT)
