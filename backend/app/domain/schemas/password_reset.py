from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetVerify(BaseModel):
    token: str = Field(..., min_length=10)


class PasswordResetComplete(BaseModel):
    token: str = Field(..., min_length=10)
    password: str = Field(..., min_length=8, max_length=100)
