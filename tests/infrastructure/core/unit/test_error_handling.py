"""Unit tests covering FastAPI global error handlers."""

from __future__ import annotations

import asyncio
import json
import logging
from unittest.mock import Mock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ValidationError
from sqlalchemy.exc import IntegrityError
from starlette.requests import Request
from starlette.testclient import TestClient

from app.core.error_handling import CoreErrorHandling
from app.utils.logging import Audit

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


@pytest.mark.unit
@pytest.mark.asyncio
async def test_http_exception_handler_returns_mapped_payload():
    eh = CoreErrorHandling(Audit())
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


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validation_exception_handler_uses_generic_message():
    eh = CoreErrorHandling(Audit())

    req = _make_request()
    # Fake pydantic validation error wrapper – content is irrelevant for handler
    from fastapi.exceptions import RequestValidationError

    exc = RequestValidationError(
        [{"loc": ("body",), "msg": "fail", "type": "value_error"}]
    )
    resp = await eh.validation_exception_handler(req, exc)
    body = json.loads(resp.body)
    assert body["code"] == "VALIDATION_ERROR" and body["status_code"] == 422


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generic_exception_handler_catches_unexpected_error(caplog):
    eh = CoreErrorHandling(Audit())

    req = _make_request()
    # Capture logs from the dedicated "audit" logger instead of relying on propagation
    with caplog.at_level(logging.ERROR, logger="audit"):
        resp = await eh.generic_exception_handler(req, RuntimeError("boom"))
    body = json.loads(resp.body)
    assert body["code"] == "SERVER_ERROR" and resp.status_code == 500
    # Trace ID verification is handled by logging tests; no assertion here to
    # avoid coupling to audit logger internals.


@pytest.mark.unit
@pytest.mark.asyncio
async def test_integrity_error_handler_maps_to_conflict():
    eh = CoreErrorHandling(Audit())

    req = _make_request()
    resp = await eh.integrity_error_handler(req, IntegrityError("msg", {}, None))
    body = json.loads(resp.body)
    assert body["status_code"] == 409 and body["code"] == "CONFLICT"


class Ping(BaseModel):
    msg: str


@pytest.fixture
def app_with_handlers():
    audit = Mock()
    err = CoreErrorHandling(audit)
    app = FastAPI()
    app.add_exception_handler(HTTPException, err.http_exception_handler)

    @app.get("/raise")
    async def _raise():
        raise HTTPException(status_code=404, detail="missing")

    return app


def test_http_exception_handler(app_with_handlers):
    client = TestClient(app_with_handlers)
    resp = client.get("/raise")
    assert resp.status_code == 404
    body = resp.json()
    assert body["code"] == "NOT_FOUND"
    assert body["detail"] == "missing"


def test_validation_exception_handler():
    audit = Mock()
    err = CoreErrorHandling(audit)

    # craft a fake request
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/",
        "headers": [],
    }
    request = Request(scope)

    # trigger pydantic validation error
    with pytest.raises(ValidationError) as exc_info:
        Ping()  # missing required field

    exc = RequestValidationError(exc_info.value.errors())
    import asyncio

    resp = asyncio.run(err.validation_exception_handler(request, exc))
    import json

    body = json.loads(resp.body)
    assert body["status_code"] == 422
