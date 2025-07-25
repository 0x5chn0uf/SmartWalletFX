"""User profile management usecase.

Encapsulates business rules for user profile operations including
profile updates, password changes, and account management.
"""
from __future__ import annotations

from typing import Optional

from app.domain.errors import InvalidCredentialsError
from app.domain.schemas.user import (
    PasswordChange,
    UserProfileRead,
    UserProfileUpdate,
)
from app.repositories.user_repository import UserRepository
from app.utils import security
from app.utils.logging import Audit


class ProfileUpdateError(Exception):
    """Raised when profile update fails due to validation or conflicts."""

    def __init__(self, field: str, message: str):
        super().__init__(message)
        self.field = field
        self.message = message


class UserProfileUsecase:
    """User profile management business logic."""

    def __init__(self, user_repository: UserRepository, audit: Audit):
        self.__user_repo = user_repository
        self.__audit = audit

    async def get_profile(self, user_id: str) -> Optional[UserProfileRead]:
        """Get user profile by ID."""
        self.__audit.info("user_profile_get_started", user_id=user_id)

        try:
            user = await self.__user_repo.get_by_id(user_id)
            if not user:
                self.__audit.warning("user_profile_get_not_found", user_id=user_id)
                return None

            self.__audit.info("user_profile_get_success", user_id=user_id)
            return UserProfileRead.model_validate(user)
        except Exception as e:
            self.__audit.error("user_profile_get_failed", user_id=user_id, error=str(e))
            raise

    async def update_profile(
        self, user_id: str, profile_update: UserProfileUpdate
    ) -> UserProfileRead:
        """Update user profile information."""
        self.__audit.info(
            "user_profile_update_started",
            user_id=user_id,
            fields=list(profile_update.model_dump(exclude_unset=True).keys()),
        )

        try:
            # Get current user
            user = await self.__user_repo.get_by_id(user_id)
            if not user:
                raise ProfileUpdateError("user", "User not found")

            # Check for username/email conflicts
            update_data = profile_update.model_dump(exclude_unset=True)

            if "username" in update_data and update_data["username"] != user.username:
                existing_user = await self.__user_repo.get_by_username(
                    update_data["username"]
                )
                if existing_user and existing_user.id != user.id:
                    raise ProfileUpdateError("username", "Username already taken")

            if "email" in update_data and update_data["email"] != user.email:
                existing_user = await self.__user_repo.get_by_email(
                    update_data["email"]
                )
                if existing_user and existing_user.id != user.id:
                    raise ProfileUpdateError("email", "Email already registered")

            # Update profile
            updated_user = await self.__user_repo.update_profile(user, update_data)

            self.__audit.info("user_profile_update_success", user_id=user_id)
            return UserProfileRead.model_validate(updated_user)

        except ProfileUpdateError:
            self.__audit.warning(
                "user_profile_update_validation_failed",
                user_id=user_id,
                error="Profile validation failed",
            )
            raise
        except Exception as e:
            self.__audit.error(
                "user_profile_update_failed", user_id=user_id, error=str(e)
            )
            raise

    async def change_password(
        self, user_id: str, password_change: PasswordChange
    ) -> bool:
        """Change user password after verifying current password."""
        self.__audit.info("user_password_change_started", user_id=user_id)

        try:
            # Get current user
            user = await self.__user_repo.get_by_id(user_id)
            if not user:
                raise InvalidCredentialsError("User not found")

            # Verify current password
            if not security.verify_password(
                password_change.current_password, user.hashed_password
            ):
                self.__audit.warning(
                    "user_password_change_invalid_current", user_id=user_id
                )
                raise InvalidCredentialsError("Current password is incorrect")

            # Hash new password
            new_hashed_password = security.get_password_hash(
                password_change.new_password
            )

            # Update password
            await self.__user_repo.change_password(user, new_hashed_password)

            self.__audit.info("user_password_change_success", user_id=user_id)
            return True

        except InvalidCredentialsError:
            self.__audit.warning("user_password_change_auth_failed", user_id=user_id)
            raise
        except Exception as e:
            self.__audit.error(
                "user_password_change_failed", user_id=user_id, error=str(e)
            )
            raise

    async def delete_account(self, user_id: str) -> bool:
        """Delete user account with all related data."""
        self.__audit.info("user_account_delete_started", user_id=user_id)

        try:
            # Get current user
            user = await self.__user_repo.get_by_id(user_id)
            if not user:
                self.__audit.warning("user_account_delete_not_found", user_id=user_id)
                return False

            # Delete user account (repository handles cascading deletes)
            await self.__user_repo.delete(user)

            self.__audit.info("user_account_delete_success", user_id=user_id)
            return True

        except Exception as e:
            self.__audit.error(
                "user_account_delete_failed", user_id=user_id, error=str(e)
            )
            raise

    async def update_notification_preferences(
        self, user_id: str, preferences: dict
    ) -> UserProfileRead:
        """Update user notification preferences."""
        self.__audit.info("user_notifications_update_started", user_id=user_id)

        try:
            user = await self.__user_repo.get_by_id(user_id)
            if not user:
                raise ProfileUpdateError("user", "User not found")

            # Validate notification preferences structure
            valid_keys = {
                "email_notifications",
                "push_notifications",
                "sms_notifications",
                "price_alerts",
                "portfolio_alerts",
                "security_alerts",
            }

            if not all(key in valid_keys for key in preferences.keys()):
                raise ProfileUpdateError(
                    "preferences", "Invalid notification preference keys"
                )

            # Update preferences
            update_data = {"notification_preferences": preferences}
            updated_user = await self.__user_repo.update_profile(user, update_data)

            self.__audit.info("user_notifications_update_success", user_id=user_id)
            return UserProfileRead.model_validate(updated_user)

        except ProfileUpdateError:
            self.__audit.warning(
                "user_notifications_update_validation_failed", user_id=user_id
            )
            raise
        except Exception as e:
            self.__audit.error(
                "user_notifications_update_failed", user_id=user_id, error=str(e)
            )
            raise
