"""User-related endpoints (protected routes)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Request, status

from app.api.dependencies import get_user_id_from_request
from app.domain.schemas.user import UserCreate, UserRead
from app.repositories.user_repository import UserRepository
from app.utils.logging import Audit


class Users:
    """Users endpoint using singleton pattern with dependency injection."""

    ep = APIRouter(prefix="/users", tags=["users"])
    __user_repo: UserRepository

    def __init__(self, user_repository: UserRepository):
        """Initialize with injected dependencies."""
        Users.__user_repo = user_repository

    @staticmethod
    @ep.get(
        "/me",
        response_model=UserRead,
        summary="Get current authenticated user profile",
    )
    async def read_current_user(request: Request) -> UserRead:
        """Return the authenticated user's public profile."""
        user_id = get_user_id_from_request(request)

        current_user = await Users.__user_repo.get_by_id(user_id)
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if hasattr(current_user, "is_active") and not getattr(
            current_user, "is_active"
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive or disabled user account",
            )

        Audit.info(
            "user_profile_view",
            user_id=str(user_id),
            ip=request.client.host if request.client else "unknown",
            path="/users/me",
        )

        return current_user

    @staticmethod
    @ep.put(
        "/{user_id}",
        response_model=UserRead,
        summary="Update a user's profile",
    )
    async def update_user(
        request: Request,
        user_id: uuid.UUID,
        user_in: UserCreate,
    ):
        """Update a user's profile."""
        current_user_id = get_user_id_from_request(request)

        user = await Users.__user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.id != current_user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        updated_user = await Users.__user_repo.update(
            user, **user_in.dict(exclude_unset=True)
        )
        return updated_user

    @staticmethod
    @ep.delete(
        "/{user_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Delete a user",
    )
    async def delete_user(
        request: Request,
        user_id: uuid.UUID,
    ):
        """Delete a user's account."""
        current_user_id = get_user_id_from_request(request)

        user = await Users.__user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.id != current_user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        await Users.__user_repo.delete(user)
        return
