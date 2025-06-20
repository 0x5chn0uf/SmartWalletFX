"""Unit tests covering app.utils.logging.audit helper."""

from __future__ import annotations

import json
import logging
import sys
import types
from io import StringIO

from app.utils import logging as audit_logging


def test_audit_logging_includes_trace_id(monkeypatch):
    """Ensure audit() attaches trace_id from structlog contextvars when present."""

    fake_ctx_module = types.SimpleNamespace(get_context=lambda: {"trace_id": "abc"})
    monkeypatch.setitem(sys.modules, "structlog.contextvars", fake_ctx_module)

    stream = StringIO()
    handler = logging.StreamHandler(stream)
    audit_logger = audit_logging._AUDIT_LOGGER  # pylint: disable=protected-access
    audit_logger.addHandler(handler)

    audit_logging.audit("unit_test", foo=1)

    audit_logger.removeHandler(handler)
    handler.flush()

    log_json = json.loads(stream.getvalue())
    assert log_json["action"] == "unit_test"
    assert log_json["trace_id"] == "abc"
    assert log_json["foo"] == 1
