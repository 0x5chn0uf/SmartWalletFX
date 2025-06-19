from __future__ import annotations

"""User-related endpoints (protected routes)."""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.dependencies import auth_deps
from app.schemas.user import UserRead
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


__all__ = ["router"]
