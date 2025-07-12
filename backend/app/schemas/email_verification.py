from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class EmailVerificationRequest(BaseModel):
    email: EmailStr


class EmailVerificationVerify(BaseModel):
    token: str = Field(..., min_length=10)
