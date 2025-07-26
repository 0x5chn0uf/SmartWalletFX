"""User-related endpoints (protected routes)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Request, UploadFile, status

from app.api.dependencies import get_user_id_from_request
from app.domain.schemas.user import (
    PasswordChange,
    UserCreate,
    UserProfileRead,
    UserProfileUpdate,
    UserRead,
)
from app.repositories.user_repository import UserRepository
from app.services.file_upload_service import FileUploadError, FileUploadService
from app.usecase.user_profile_usecase import (
    ProfileUpdateError,
    UserProfileUsecase,
)
from app.utils.logging import Audit


class Users:
    """Users endpoint using singleton pattern with dependency injection."""

    ep = APIRouter(prefix="/users", tags=["users"])
    __user_repo: UserRepository
    __user_profile_usecase: UserProfileUsecase
    __file_upload_service: FileUploadService

    def __init__(
        self,
        user_repository: UserRepository,
        user_profile_usecase: UserProfileUsecase,
        file_upload_service: FileUploadService,
    ):
        """Initialize with injected dependencies."""
        Users.__user_repo = user_repository
        Users.__user_profile_usecase = user_profile_usecase
        Users.__file_upload_service = file_upload_service

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

        if hasattr(current_user, "is_active") and not current_user.is_active:
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

    @staticmethod
    @ep.get(
        "/me/profile",
        response_model=UserProfileRead,
        summary="Get current user's detailed profile",
    )
    async def get_user_profile(request: Request) -> UserProfileRead:
        """Get the authenticated user's detailed profile information."""
        user_id = get_user_id_from_request(request)

        try:
            profile = await Users.__user_profile_usecase.get_profile(str(user_id))
            if not profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User profile not found",
                )

            Audit.info(
                "user_profile_retrieved",
                user_id=str(user_id),
                ip=request.client.host if request.client else "unknown",
                path="/users/me/profile",
            )

            return profile
        except Exception as e:
            Audit.error(
                "user_profile_retrieval_failed", user_id=str(user_id), error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user profile",
            )

    @staticmethod
    @ep.put(
        "/me/profile",
        response_model=UserProfileRead,
        summary="Update current user's profile",
    )
    async def update_user_profile(
        request: Request, profile_update: UserProfileUpdate
    ) -> UserProfileRead:
        """Update the authenticated user's profile information."""
        user_id = get_user_id_from_request(request)

        try:
            updated_profile = await Users.__user_profile_usecase.update_profile(
                str(user_id), profile_update
            )

            Audit.info(
                "user_profile_updated",
                user_id=str(user_id),
                ip=request.client.host if request.client else "unknown",
                path="/users/me/profile",
                fields=list(profile_update.model_dump(exclude_unset=True).keys()),
            )

            return updated_profile

        except ProfileUpdateError as e:
            Audit.warning(
                "user_profile_update_validation_error",
                user_id=str(user_id),
                field=e.field,
                error_message=e.message,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Profile update failed: {e.message}",
            )
        except Exception as e:
            Audit.error(
                "user_profile_update_failed", user_id=str(user_id), error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user profile",
            )

    @staticmethod
    @ep.post(
        "/me/change-password",
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Change current user's password",
    )
    async def change_password(request: Request, password_change: PasswordChange):
        """Change the authenticated user's password."""
        user_id = get_user_id_from_request(request)

        try:
            await Users.__user_profile_usecase.change_password(
                str(user_id), password_change
            )

            Audit.info(
                "user_password_changed",
                user_id=str(user_id),
                ip=request.client.host if request.client else "unknown",
                path="/users/me/change-password",
            )

        except Exception as e:
            if "Current password is incorrect" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect",
                )
            Audit.error(
                "user_password_change_failed", user_id=str(user_id), error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to change password",
            )

    @staticmethod
    @ep.put(
        "/me/notifications",
        response_model=UserProfileRead,
        summary="Update notification preferences",
    )
    async def update_notification_preferences(
        request: Request, preferences: dict
    ) -> UserProfileRead:
        """Update the authenticated user's notification preferences."""
        user_id = get_user_id_from_request(request)

        try:
            updated_profile = (
                await Users.__user_profile_usecase.update_notification_preferences(
                    str(user_id), preferences
                )
            )

            Audit.info(
                "user_notifications_updated",
                user_id=str(user_id),
                ip=request.client.host if request.client else "unknown",
                path="/users/me/notifications",
            )

            return updated_profile

        except ProfileUpdateError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Notification preferences update failed: {e.message}",
            )
        except Exception as e:
            Audit.error(
                "user_notifications_update_failed", user_id=str(user_id), error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update notification preferences",
            )

    @staticmethod
    @ep.delete(
        "/me",
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Delete current user's account",
    )
    async def delete_current_user_account(request: Request):
        """Delete the authenticated user's account and all associated data."""
        user_id = get_user_id_from_request(request)

        try:
            success = await Users.__user_profile_usecase.delete_account(str(user_id))
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User account not found",
                )

            Audit.info(
                "user_account_deleted",
                user_id=str(user_id),
                ip=request.client.host if request.client else "unknown",
                path="/users/me",
            )

        except Exception as e:
            Audit.error(
                "user_account_deletion_failed", user_id=str(user_id), error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user account",
            )

    @staticmethod
    @ep.post(
        "/me/profile/picture",
        response_model=dict,
        summary="Upload profile picture",
    )
    async def upload_profile_picture(request: Request, file: UploadFile) -> dict:
        """Upload a profile picture for the authenticated user."""
        user_id = get_user_id_from_request(request)

        try:
            # Upload file and get URL
            file_url = await Users.__file_upload_service.upload_profile_picture(
                file, str(user_id)
            )

            # Update user profile with new picture URL
            profile_update = UserProfileUpdate(profile_picture_url=file_url)
            await Users.__user_profile_usecase.update_profile(
                str(user_id), profile_update
            )

            Audit.info(
                "profile_picture_uploaded",
                user_id=str(user_id),
                ip=request.client.host if request.client else "unknown",
                path="/users/me/profile/picture",
                file_url=file_url,
            )

            return {
                "message": "Profile picture uploaded successfully",
                "profile_picture_url": file_url,
            }

        except FileUploadError as e:
            Audit.warning(
                "profile_picture_upload_validation_error",
                user_id=str(user_id),
                error=e.message,
                code=e.code,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File upload failed: {e.message}",
            )
        except Exception as e:
            Audit.error(
                "profile_picture_upload_failed", user_id=str(user_id), error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload profile picture",
            )
