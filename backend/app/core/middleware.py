"""Custom FastAPI / Starlette middleware utilities (core layer)."""

from __future__ import annotations

import uuid

import structlog
from fastapi import Request, Response
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)

logger = structlog.get_logger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Attach a per-request *trace_id* (UUID4) to request, response, and log context."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:  # type: ignore[override]
        trace_id = str(uuid.uuid4())

        # Bind to structlog contextvars for automatic inclusion
        structlog.contextvars.bind_contextvars(trace_id=trace_id)
        request.state.trace_id = trace_id

        # Process downstream handlers
        response: Response = await call_next(request)

        # Propagate trace_id header for clients
        response.headers["X-Trace-Id"] = trace_id

        # Cleanup – avoid leaking context into next request in workers
        structlog.contextvars.unbind_contextvars("trace_id")

        return response
