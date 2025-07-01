from __future__ import annotations

"""Repository layer for User entity interactions.

Provides a thin abstraction around the SQLAlchemy session to keep the
application/service layer free from ORM specifics. This aligns with the
project's hexagonal architecture where repositories are infrastructure
concerns injected into the domain/application layers.
"""

import uuid
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User


class UserRepository:
    """Asynchronous repository for CRUD operations on :class:`~app.models.user.User`."""

    def __init__(self, session: AsyncSession):
        self._session = session

    # ---------------------------------------------------------------------
    # Query helpers
    # ---------------------------------------------------------------------

    async def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(User).filter_by(username=username)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).filter_by(email=email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists(
        self, *, username: str | None = None, email: str | None = None
    ) -> bool:
        """Return True if a user exists with the given username or email."""

        stmt = select(User.id)
        if username is not None:
            stmt = stmt.filter_by(username=username)
        if email is not None:
            stmt = stmt.filter_by(email=email)
        result = await self._session.execute(stmt.limit(1))
        return result.scalar_one_or_none() is not None

    async def get_by_id(self, user_id):  # type: ignore[override]
        """Return the :class:`User` identified by *user_id* or **None**.

        Accepts *str* or :class:`uuid.UUID` for convenience so callers can
        safely pass the **sub** claim from a JWT without manual casting.
        """

        if isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except ValueError:
                # Leave as string for DBs that store UUIDs as TEXT
                pass

        return await self._session.get(User, user_id)

    # ---------------------------------------------------------------------
    # Persistence helpers
    # ---------------------------------------------------------------------

    async def save(self, user: User) -> User:
        """Persist *user* instance and commit the transaction."""

        self._session.add(user)
        try:
            await self._session.commit()
        except IntegrityError:  # safeguard against race-condition duplicates
            await self._session.rollback()
            raise
        await self._session.refresh(user)
        return user
