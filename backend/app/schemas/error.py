"""Shared error response schema used across API endpoints."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standardised error response envelope."""

    detail: str = Field(..., description="Human-readable error message")
    code: str = Field(..., description="Machine-readable error code")
    status_code: int = Field(..., description="HTTP status code")
    trace_id: str = Field(..., description="Request correlation identifier")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "detail": "Invalid username or password",
                    "code": "AUTH_FAILURE",
                    "status_code": 401,
                    "trace_id": "7f580fb3-4d94-4b95-9d0b-87850c2c7399",
                }
            ]
        }
    }
