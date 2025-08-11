import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from app.core.middleware import CorrelationIdMiddleware


def _create_app():
    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)

    @app.get("/ping")
    async def ping():
        return {"ok": True}

    return app


def test_trace_id_header_present():
    app = _create_app()
    client = TestClient(app)
    resp = client.get("/ping")
    assert resp.status_code == 200
    assert "X-Trace-Id" in resp.headers
    trace_id = resp.headers["X-Trace-Id"]
    # header should be 32-char hex uuid
    assert len(trace_id) in (32, 36)
