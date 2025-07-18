"""FastAPI global exception handlers producing consistent JSON ErrorResponse."""

from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.schemas.error import ErrorResponse
from app.schemas.user import WeakPasswordError
from app.utils.logging import Audit

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
    Audit.error("http_exception", **payload)
    return JSONResponse(status_code=exc.status_code, content=payload)


async def validation_exception_handler(request: Request, exc: RequestValidationError):  # type: ignore[valid-type]  # noqa: E501
    trace_id = _get_trace_id(request)
    payload = ErrorResponse(  # noqa: E501
        detail="Invalid request payload",
        code="VALIDATION_ERROR",
        status_code=422,
        trace_id=trace_id,
    ).model_dump()
    Audit.error("validation_error", **payload)
    return JSONResponse(status_code=422, content=payload)


async def generic_exception_handler(request: Request, exc: Exception):  # type: ignore[valid-type]  # noqa: E501
    trace_id = _get_trace_id(request)
    Audit.error("unhandled_exception", trace_id=trace_id, exc_info=exc)
    payload = ErrorResponse(  # noqa: E501
        detail="Internal server error",
        code="SERVER_ERROR",
        status_code=500,
        trace_id=trace_id,
    ).model_dump()
    return JSONResponse(status_code=500, content=payload)


async def integrity_error_handler(request: Request, exc: IntegrityError):  # type: ignore[valid-type]  # noqa: E501
    trace_id = _get_trace_id(request)
    payload = ErrorResponse(  # noqa: E501
        detail="Resource conflict",
        code="CONFLICT",
        status_code=409,
        trace_id=trace_id,
    ).model_dump()
    Audit.warning("db_conflict", **payload)
    return JSONResponse(status_code=409, content=payload)


async def weak_password_error_handler(
    request: Request, exc: WeakPasswordError
):  # type: ignore[valid-type]
    """Return 400 BAD_REQUEST when password strength validation fails."""

    trace_id = _get_trace_id(request)
    payload = ErrorResponse(
        detail=exc.detail,
        code="BAD_REQUEST",
        status_code=400,
        trace_id=trace_id,
    ).model_dump()
    Audit.warning("weak_password", **payload)
    return JSONResponse(status_code=400, content=payload)


__all__ = [
    "http_exception_handler",
    "validation_exception_handler",
    "generic_exception_handler",
    "integrity_error_handler",
    "weak_password_error_handler",
]
