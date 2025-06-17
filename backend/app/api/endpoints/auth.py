from __future__ import annotations

"""Authentication endpoints (registration only – Subtask 4.5)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, oauth2_scheme
from app.core.database import get_db
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import (
    AuthService,
    DuplicateError,
    WeakPasswordError,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserRead,
    summary="Register a new user",
)
async def register_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserRead:  # type: ignore[valid-type]
    """Create a new user account.

    Returns the newly-created user object excluding sensitive fields.
    """

    service = AuthService(db)
    try:
        user = await service.register(payload)
    except DuplicateError as dup:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{dup.field} already exists",
        ) from dup
    except WeakPasswordError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet strength requirements",
        )

    return user


# Re-export for convenience in other modules
__all__ = ["router", "oauth2_scheme", "get_current_user"]
