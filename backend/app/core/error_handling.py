"""FastAPI global exception handlers producing consistent JSON ErrorResponse."""

from __future__ import annotations

from typing import Final

import structlog
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.schemas.error import ErrorResponse

_LOGGER: Final = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def _get_trace_id(request: Request) -> str:
    return getattr(request.state, "trace_id", "unknown")


# ---------------------------------------------------------------------------
# Exception Handlers
# ---------------------------------------------------------------------------

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


async def http_exception_handler(request: Request, exc: HTTPException):  # type: ignore[valid-type]  # noqa: E501
    trace_id = _get_trace_id(request)

    code = _CODE_MAP.get(exc.status_code, "ERROR")
    payload = ErrorResponse(  # noqa: E501 – acceptable length for readability
        detail=exc.detail,
        code=code,
        status_code=exc.status_code,
        trace_id=trace_id,
    ).model_dump()
    _LOGGER.info("http_exception", **payload)
    return JSONResponse(status_code=exc.status_code, content=payload)


async def validation_exception_handler(request: Request, exc: RequestValidationError):  # type: ignore[valid-type]  # noqa: E501
    trace_id = _get_trace_id(request)
    payload = ErrorResponse(  # noqa: E501
        detail="Invalid request payload",
        code="VALIDATION_ERROR",
        status_code=422,
        trace_id=trace_id,
    ).model_dump()
    _LOGGER.info("validation_error", **payload)
    return JSONResponse(status_code=422, content=payload)


async def generic_exception_handler(request: Request, exc: Exception):  # type: ignore[valid-type]  # noqa: E501
    trace_id = _get_trace_id(request)
    _LOGGER.error("unhandled_exception", trace_id=trace_id, exc_info=exc)
    payload = ErrorResponse(  # noqa: E501
        detail="Internal server error",
        code="SERVER_ERROR",
        status_code=500,
        trace_id=trace_id,
    ).model_dump()
    return JSONResponse(status_code=500, content=payload)


# Additional handler for DB conflicts -------------------------------------------------


async def integrity_error_handler(request: Request, exc: IntegrityError):  # type: ignore[valid-type]  # noqa: E501
    trace_id = _get_trace_id(request)
    payload = ErrorResponse(  # noqa: E501
        detail="Resource conflict",
        code="CONFLICT",
        status_code=409,
        trace_id=trace_id,
    ).model_dump()
    _LOGGER.info("db_conflict", **payload)
    return JSONResponse(status_code=409, content=payload)


__all__ = [
    "http_exception_handler",
    "validation_exception_handler",
    "generic_exception_handler",
    "integrity_error_handler",
]
