"""Schemas related to authentication token issuance.

These are **temporary stubs** added during the red phase of TDD for
Subtask 4.8.  They intentionally raise :class:`NotImplementedError` so
that newly-scaffolded tests fail until the actual implementation is
completed.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    """Successful response from ``POST /auth/token``."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type, always 'bearer'.")
    expires_in: int = Field(..., description="Access token lifetime in seconds.")
    refresh_token: str = Field(..., description="JWT refresh token")
