"""Repository layer for User entity interactions.

Provides a thin abstraction around the SQLAlchemy session to keep the
application/service layer free from ORM specifics. This aligns with the
project's hexagonal architecture where repositories are infrastructure
concerns injected into the domain/application layers.
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.utils.logging import Audit


class UserRepository:
    """Asynchronous repository for CRUD operations on :class:`~app.models.user.User`."""

    def __init__(self, session: AsyncSession):
        self._session = session

    # ---------------------------------------------------------------------
    # Query helpers
    # ---------------------------------------------------------------------

    async def get_all(self) -> list[User]:
        """Return all users in the database."""
        stmt = select(User)
        result = await self._session.execute(stmt)
        return result.scalars().all()

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

    async def save(self, user: User) -> User:
        """Persist *user* instance and commit the transaction."""
        self._session.add(user)
        try:
            await self._session.commit()
        except IntegrityError as e:  # safeguard against race-condition duplicates
            Audit.error("User already exists", error=e)
            await self._session.rollback()
            raise

        await self._session.refresh(user)
        return user

    async def update(self, user: User, **kwargs) -> User:
        """Update *user* with provided fields and commit changes.

        Parameters
        ----------
        user:
            The managed :class:`~app.models.user.User` instance to update.
        **kwargs:
            Attribute-value pairs to update. Keys that do not correspond to
            columns on the model are silently ignored to avoid runtime errors
            from e.g. PATCH-like payloads including unrelated metadata.
        """

        for field, value in kwargs.items():
            if hasattr(user, field):
                setattr(user, field, value)

        try:
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise

        await self._session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        """Delete *user* from the database and commit."""

        await self._session.execute(  # type: ignore[arg-type]
            delete(RefreshToken).where(RefreshToken.user_id == user.id)
        )

        await self._session.delete(user)
        await self._session.commit()
