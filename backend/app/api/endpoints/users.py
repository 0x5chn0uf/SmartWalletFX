"""User-related endpoints (protected routes)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.dependencies import auth_deps, get_db
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserRead
from app.utils.logging import audit

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current authenticated user profile",
)
async def read_current_user(
    request: Request,
    current_user=Depends(auth_deps.get_current_user),  # type: ignore[valid-type]
) -> UserRead:  # type: ignore[valid-type]
    """Return the authenticated user's public profile.

    Raises 403 if the account is flagged inactive/disabled (expects the SQLAlchemy
    model to expose an ``is_active`` boolean – defaults to *True* if missing).
    """

    # Enforce active status if attribute exists
    if hasattr(current_user, "is_active") and not getattr(current_user, "is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive or disabled user account",
        )

    # Structured audit log
    audit(
        "user_profile_view",
        user_id=str(getattr(current_user, "id", "unknown")),
        ip=request.client.host if request.client else "unknown",
        path="/users/me",
    )

    return current_user


@router.put(
    "/{user_id}",
    response_model=UserRead,
    summary="Update a user's profile",
)
async def update_user(
    user_id: uuid.UUID,
    user_in: UserCreate,
    db=Depends(get_db),
    current_user=Depends(auth_deps.get_current_user),
):
    """Update a user's profile."""
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # For now, only allow users to update their own profile
    if user.id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    updated_user = await repo.update(user, **user_in.dict(exclude_unset=True))
    return updated_user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user",
)
async def delete_user(
    user_id: uuid.UUID,
    db=Depends(get_db),
    current_user=Depends(auth_deps.get_current_user),
):
    """Delete a user's account."""
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # For now, only allow users to delete their own profile
    if user.id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    await repo.delete(user)
    return


__all__ = ["router"]
