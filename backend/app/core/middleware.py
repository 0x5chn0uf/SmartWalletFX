"""Custom FastAPI / Starlette middleware utilities (core layer)."""

from __future__ import annotations

import uuid
from typing import Optional

import structlog
from fastapi import Request, Response
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)

from app.utils.logging import Audit


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Attach a per-request *trace_id* (UUID4) to request, response, and log context."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:  # type: ignore[override]
        trace_id = str(uuid.uuid4())

        # Bind to structlog contextvars for automatic inclusion
        structlog.contextvars.bind_contextvars(trace_id=trace_id)
        request.state.trace_id = trace_id

        # Process downstream handlers with proper exception handling for
        # BaseHTTPMiddleware
        try:
            response: Response = await call_next(request)
            # Include correlation ID in response header
            response.headers["X-Trace-ID"] = trace_id
            return response
        except Exception as exc:
            # For HTTPExceptions, we need to create a proper response
            from fastapi import HTTPException
            from fastapi.responses import JSONResponse

            if isinstance(exc, HTTPException):
                # Create a proper response for HTTPException to prevent
                # "No response returned"
                from app.domain.schemas.error import ErrorResponse

                code_map = {
                    400: "BAD_REQUEST",
                    401: "AUTH_FAILURE",
                    403: "AUTH_FAILURE",
                    404: "NOT_FOUND",
                    409: "CONFLICT",
                    422: "VALIDATION_ERROR",
                    429: "RATE_LIMIT",
                }
                code = code_map.get(exc.status_code, "ERROR")

                payload = ErrorResponse(
                    detail=exc.detail,
                    code=code,
                    status_code=exc.status_code,
                    trace_id=trace_id,
                ).model_dump()

                response = JSONResponse(status_code=exc.status_code, content=payload)
                response.headers["X-Trace-ID"] = trace_id
                return response
            else:
                # For other exceptions, re-raise to let FastAPI's exception
                # handlers deal with it
                raise


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """Extract user_id from JWT token and add it to request state."""

    def __init__(self, app, di_container=None, protected_paths: Optional[list] = None):
        super().__init__(app)
        self.di_container = di_container
        # Define which paths require authentication
        self.protected_paths = protected_paths or [
            "/users",
            "/wallets",
            "/admin",
        ]
        # Paths that should be excluded from auth
        self.excluded_paths = [
            "/auth/token",
            "/auth/refresh",
            "/oauth/",
            "/health",
            "/jwks",
            "/docs",
            "/openapi.json",
            "/redoc",
        ]

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:  # type: ignore[override]
        # Initialize user_id as None
        request.state.user_id = None

        # Check if this path requires authentication
        path = request.url.path
        requires_auth = any(
            path.startswith(protected) for protected in self.protected_paths
        )
        is_excluded = any(path.startswith(excluded) for excluded in self.excluded_paths)

        if not requires_auth or is_excluded:
            # Skip auth for non-protected or excluded paths
            return await call_next(request)

        # Extract token from Authorization header or cookies
        token = None

        # First try Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

        # If no Authorization header, try access_token cookie
        if not token:
            token = request.cookies.get("access_token")

        if not token:
            # Let the endpoint handle the 401 error
            return await call_next(request)

        try:
            # Use the injected DI container or fall back to global import
            if self.di_container:
                jwt_utils = self.di_container.get_utility("jwt_utils")
            else:
                # Local import to avoid circular dependency
                from app.main import di_container

                jwt_utils = di_container.get_utility("jwt_utils")

            # Decode token and extract user_id
            payload = jwt_utils.decode_token(token)
            user_id = uuid.UUID(str(payload["sub"]))

            # Add user_id to request state
            request.state.user_id = user_id
            request.state.token_payload = payload

        except Exception as exc:
            # Log the error but let the endpoint handle the auth failure
            Audit.warning("JWT auth middleware failed", error=str(exc))
            # Leave user_id as None, endpoint can check this

        # Continue to endpoint
        return await call_next(request)


class Middleware:
    """Service for managing FastAPI middleware components."""

    def __init__(self, audit: Audit):
        """Initialize middleware service with audit logging."""
        self.audit = audit

    def get_correlation_id_middleware(self) -> type[CorrelationIdMiddleware]:
        """Get the correlation ID middleware class."""
        return CorrelationIdMiddleware

    def create_correlation_id_middleware(self) -> CorrelationIdMiddleware:
        """Create a new instance of correlation ID middleware."""
        return CorrelationIdMiddleware(app=None)  # app will be set by FastAPI

    def get_jwt_auth_middleware(self) -> type[JWTAuthMiddleware]:
        """Get the JWT Auth middleware class."""
        return JWTAuthMiddleware

    def create_jwt_auth_middleware(self, di_container=None) -> JWTAuthMiddleware:
        """Create a new instance of JWT Auth middleware."""
        # app will be set by FastAPI
        return JWTAuthMiddleware(app=None, di_container=di_container)
