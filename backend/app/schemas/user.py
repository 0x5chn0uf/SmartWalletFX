from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.utils.security import validate_password_strength


class UserBase(BaseModel):
    """Common fields shared by all user-facing schemas."""

    id: int
    username: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    """Schema used when registering a new user (API input)."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Plaintext user password (will be hashed)",
    )

    @field_validator("password")
    @classmethod
    def check_strength(cls, v: str) -> str:  # noqa: D401
        if not validate_password_strength(v):
            raise ValueError(
                "Password must be at least 8 characters and include a digit and symbol"
            )
        return v


class UserRead(UserBase):
    """Schema returned by API responses (password omitted)."""

    pass


class UserInDB(UserBase):
    """Internal schema that includes hashed password for repository interactions."""

    hashed_password: str
