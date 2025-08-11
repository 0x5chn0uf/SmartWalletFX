from __future__ import annotations

"""Pydantic model for validated JWT payloads."""

from datetime import datetime
from typing import Any, Dict, List

from pydantic import UUID4, BaseModel, field_validator


class JWTPayload(BaseModel):
    """Schema representing the expected JWT payload."""

    sub: UUID4
    exp: int
    iat: int
    jti: str
    type: str = "access"
    roles: List[str] = []
    attributes: Dict[str, Any] = {}

    model_config = {"extra": "allow", "validate_assignment": True}

    @field_validator("exp")
    @classmethod
    def validate_exp(cls, v: int) -> int:  # noqa: D401
        """Ensure *exp* timestamp is in the future."""
        if v <= int(datetime.now().timestamp()):
            raise ValueError("Token has expired")
        return v
