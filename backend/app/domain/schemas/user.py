from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.utils.security import validate_password_strength


class WeakPasswordError(Exception):
    """Raised when a password does not meet strength requirements."""

    def __init__(self, detail: str = "Password does not meet strength requirements"):
        self.detail = detail
        super().__init__(detail)


class UserBase(BaseModel):
    """Common fields shared by all user-facing app.domain.schemas."""

    id: uuid.UUID
    username: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime
    email_verified: bool

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    """Schema used when registering a new user (API input)."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(
        ...,
        description="Plaintext user password (will be hashed)",
    )

    @field_validator("password")
    @classmethod
    def check_strength(cls, v: str) -> str:  # noqa: D401
        if not validate_password_strength(v):
            raise ValueError("Password does not meet strength requirements")
        return v


class UserRead(UserBase):
    """Schema returned by API responses (password omitted)."""

    pass


class UserInDB(UserBase):
    """Internal schema that includes hashed password for repository interactions."""

    hashed_password: str


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile information."""

    username: str | None = Field(None, min_length=3, max_length=50)
    email: EmailStr | None = None
    profile_picture_url: str | None = Field(None, max_length=500)
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    bio: str | None = Field(None, max_length=1000)
    timezone: str | None = Field(None, max_length=50)
    preferred_currency: str | None = Field(None, max_length=10)
    notification_preferences: dict | None = None

    model_config = {"from_attributes": True}


class PasswordChange(BaseModel):
    """Schema for changing user password."""

    current_password: str = Field(
        ..., min_length=1, description="Current password for verification"
    )
    new_password: str = Field(..., description="New password (will be hashed)")

    @field_validator("new_password")
    @classmethod
    def check_strength(cls, v: str) -> str:
        if not validate_password_strength(v):
            raise ValueError("Password does not meet strength requirements")
        return v


class UserProfileRead(UserBase):
    """Extended user profile schema for API responses."""

    profile_picture_url: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    bio: str | None = None
    timezone: str | None = None
    preferred_currency: str | None = None
    notification_preferences: dict | None = None
