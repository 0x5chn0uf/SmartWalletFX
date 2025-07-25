from __future__ import annotations

import pytest

from app.domain.schemas.audit_log import AuditEventBase


@pytest.mark.unit
def test_roundtrip_identity() -> None:
    sample = {
        "timestamp": "2025-06-20T12:00:00Z",
        "action": "user_login_success",
        "result": "success",
    }
    model = AuditEventBase(**sample)
    # Ensure model_dump round-trips to the same keys/values (plus auto-fields)
    dumped = model.model_dump(mode="json")
    for k, v in sample.items():
        assert dumped[k] == v
