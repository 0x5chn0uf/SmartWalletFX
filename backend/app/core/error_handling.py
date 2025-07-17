"""Error handling service for FastAPI global exception handlers."""

from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.domain.schemas.error import ErrorResponse
from app.domain.schemas.user import WeakPasswordError
from app.utils.logging import Audit


class CoreErrorHandling:
    """Service for handling global exceptions in FastAPI applications."""

    def __init__(self, audit: Audit):
        """Initialize error handling service with audit logging."""
        self.audit = audit

    def _get_trace_id(self, request: Request) -> str:
        """Get trace ID from request state."""
        return getattr(request.state, "trace_id", "unknown")

    # Map status codes to error codes
    _CODE_MAP = {
        400: "BAD_REQUEST",
        401: "AUTH_FAILURE",
        403: "AUTH_FAILURE",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT",
    }

    async def http_exception_handler(
        self, request: Request, exc: HTTPException
    ) -> JSONResponse:
        """Handle HTTP exceptions."""
        trace_id = self._get_trace_id(request)

        code = self._CODE_MAP.get(exc.status_code, "ERROR")
        payload = ErrorResponse(
            detail=exc.detail,
            code=code,
            status_code=exc.status_code,
            trace_id=trace_id,
        ).model_dump()
        self.audit.error("http_exception", **payload)
        return JSONResponse(status_code=exc.status_code, content=payload)

    async def validation_exception_handler(
        self, request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle validation exceptions."""
        trace_id = self._get_trace_id(request)
        payload = ErrorResponse(
            detail="Invalid request payload",
            code="VALIDATION_ERROR",
            status_code=422,
            trace_id=trace_id,
        ).model_dump()
        self.audit.error("validation_error", **payload)
        return JSONResponse(status_code=422, content=payload)

    async def generic_exception_handler(
        self, request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle generic exceptions."""
        trace_id = self._get_trace_id(request)
        self.audit.error("unhandled_exception", trace_id=trace_id, exc_info=exc)
        payload = ErrorResponse(
            detail="Internal server error",
            code="SERVER_ERROR",
            status_code=500,
            trace_id=trace_id,
        ).model_dump()
        return JSONResponse(status_code=500, content=payload)

    async def integrity_error_handler(
        self, request: Request, exc: IntegrityError
    ) -> JSONResponse:
        """Handle database integrity errors."""
        trace_id = self._get_trace_id(request)
        payload = ErrorResponse(
            detail="Resource conflict",
            code="CONFLICT",
            status_code=409,
            trace_id=trace_id,
        ).model_dump()
        self.audit.warning("db_conflict", **payload)
        return JSONResponse(status_code=409, content=payload)

    async def weak_password_error_handler(
        self, request: Request, exc: WeakPasswordError
    ) -> JSONResponse:
        """Handle weak password errors."""
        trace_id = self._get_trace_id(request)
        payload = ErrorResponse(
            detail=exc.detail,
            code="BAD_REQUEST",
            status_code=400,
            trace_id=trace_id,
        ).model_dump()
        self.audit.warning("weak_password", **payload)
        return JSONResponse(status_code=400, content=payload)
