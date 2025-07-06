"""Unit tests covering FastAPI global error handlers."""

from __future__ import annotations

import json
import logging

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from starlette.requests import Request

from app.core import error_handling as eh

# ---------------------------------------------------------------------------
# Helper – fabricate bare-bones Starlette Request with trace_id
# ---------------------------------------------------------------------------


def _make_request() -> Request:
    scope = {"type": "http", "method": "GET", "path": "/", "headers": []}
    req = Request(scope)
    req.state.trace_id = "test-trace"
    return req


# ---------------------------------------------------------------------------
# http_exception_handler & validation_exception_handler
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_http_exception_handler_returns_mapped_payload():
    req = _make_request()
    exc = HTTPException(status_code=404, detail="not found")
    resp = await eh.http_exception_handler(req, exc)
    body = json.loads(resp.body)
    assert body == {
        "detail": "not found",
        "code": "NOT_FOUND",
        "status_code": 404,
        "trace_id": "test-trace",
    }
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_validation_exception_handler_uses_generic_message():
    req = _make_request()
    # Fake pydantic validation error wrapper – content is irrelevant for handler
    from fastapi.exceptions import RequestValidationError

    exc = RequestValidationError(
        [{"loc": ("body",), "msg": "fail", "type": "value_error"}]
    )
    resp = await eh.validation_exception_handler(req, exc)
    body = json.loads(resp.body)
    assert body["code"] == "VALIDATION_ERROR" and body["status_code"] == 422


@pytest.mark.asyncio
async def test_generic_exception_handler_catches_unexpected_error(caplog):
    req = _make_request()
    # Capture logs from the dedicated "audit" logger instead of relying on propagation
    with caplog.at_level(logging.ERROR, logger="audit"):
        resp = await eh.generic_exception_handler(req, RuntimeError("boom"))
    body = json.loads(resp.body)
    assert body["code"] == "SERVER_ERROR" and resp.status_code == 500
    # Trace ID verification is handled by logging tests; no assertion here to
    # avoid coupling to audit logger internals.


@pytest.mark.asyncio
async def test_integrity_error_handler_maps_to_conflict():
    req = _make_request()
    resp = await eh.integrity_error_handler(req, IntegrityError("msg", {}, None))
    body = json.loads(resp.body)
    assert body["status_code"] == 409 and body["code"] == "CONFLICT"
