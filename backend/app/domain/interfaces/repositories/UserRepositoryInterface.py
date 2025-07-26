from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.models.user import User


class UserRepositoryInterface(ABC):
    """Interface for user persistence."""

    @abstractmethod
    async def get_all(self) -> List[User]:  # pragma: no cover
        """Return all users."""

    @abstractmethod
    async def get_by_username(
        self, username: str
    ) -> Optional[User]:  # pragma: no cover
        """Retrieve a user by username."""

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:  # pragma: no cover
        """Retrieve a user by email."""

    @abstractmethod
    async def exists(
        self, *, username: str | None = None, email: str | None = None
    ) -> bool:  # pragma: no cover
        """Return True if a user exists matching the provided criteria."""

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:  # pragma: no cover
        """Retrieve a user by id."""

    @abstractmethod
    async def save(self, user: User) -> User:  # pragma: no cover
        """Persist a new user instance."""

    @abstractmethod
    async def update(self, user: User, **kwargs) -> User:  # pragma: no cover
        """Update fields on the given user."""

    @abstractmethod
    async def delete(self, user: User) -> None:  # pragma: no cover
        """Delete the provided user."""

    @abstractmethod
    async def update_profile(
        self, user: User, profile_data: dict
    ) -> User:  # pragma: no cover
        """Update user profile data."""

    @abstractmethod
    async def change_password(
        self, user: User, new_hashed_password: str
    ) -> User:  # pragma: no cover
        """Change the user's password."""
