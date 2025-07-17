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
from sqlalchemy.future import select

from app.core.database import CoreDatabase
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.utils.logging import Audit


class UserRepository:
    """Asynchronous repository for CRUD operations on :class:`~app.models.user.User`."""

    def __init__(self, database: CoreDatabase, audit: Audit):
        self.__database = database
        self.__audit = audit

    # ---------------------------------------------------------------------
    # Query helpers
    # ---------------------------------------------------------------------

    async def get_all(self) -> list[User]:
        """Return all users in the database."""
        self.__audit.info("user_repository_get_all_started")

        try:
            async with self.__database.get_session() as session:
                stmt = select(User)
                result = await session.execute(stmt)
                users = result.scalars().all()

                self.__audit.info(
                    "user_repository_get_all_success", user_count=len(users)
                )
                return users
        except Exception as e:
            self.__audit.error("user_repository_get_all_failed", error=str(e))
            raise

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        self.__audit.info("user_repository_get_by_username_started", username=username)

        try:
            async with self.__database.get_session() as session:
                stmt = select(User).filter_by(username=username)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()

                self.__audit.info(
                    "user_repository_get_by_username_success",
                    username=username,
                    found=user is not None,
                )
                return user
        except Exception as e:
            self.__audit.error(
                "user_repository_get_by_username_failed",
                username=username,
                error=str(e),
            )
            raise

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        self.__audit.info("user_repository_get_by_email_started", email=email)

        try:
            async with self.__database.get_session() as session:
                stmt = select(User).filter_by(email=email)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()

                self.__audit.info(
                    "user_repository_get_by_email_success",
                    email=email,
                    found=user is not None,
                )
                return user
        except Exception as e:
            self.__audit.error(
                "user_repository_get_by_email_failed", email=email, error=str(e)
            )
            raise

    async def exists(
        self, *, username: str | None = None, email: str | None = None
    ) -> bool:
        """Return True if a user exists with the given username or email."""
        self.__audit.info(
            "user_repository_exists_started", username=username, email=email
        )

        try:
            async with self.__database.get_session() as session:
                stmt = select(User.id)
                if username is not None:
                    stmt = stmt.filter_by(username=username)
                if email is not None:
                    stmt = stmt.filter_by(email=email)
                result = await session.execute(stmt.limit(1))
                exists = result.scalar_one_or_none() is not None

                self.__audit.info(
                    "user_repository_exists_success",
                    username=username,
                    email=email,
                    exists=exists,
                )
                return exists
        except Exception as e:
            self.__audit.error(
                "user_repository_exists_failed",
                username=username,
                email=email,
                error=str(e),
            )
            raise

    async def get_by_id(self, user_id) -> Optional[User]:  # type: ignore[override]
        """Return the :class:`User` identified by *user_id* or **None**.

        Accepts *str* or :class:`uuid.UUID` for convenience so callers can
        safely pass the **sub** claim from a JWT without manual casting.
        """
        self.__audit.info("user_repository_get_by_id_started", user_id=str(user_id))

        try:
            if isinstance(user_id, str):
                try:
                    user_id = uuid.UUID(user_id)
                except ValueError:
                    # Leave as string for DBs that store UUIDs as TEXT
                    pass

            async with self.__database.get_session() as session:
                user = await session.get(User, user_id)

                self.__audit.info(
                    "user_repository_get_by_id_success",
                    user_id=str(user_id),
                    found=user is not None,
                )
                return user
        except Exception as e:
            self.__audit.error(
                "user_repository_get_by_id_failed", user_id=str(user_id), error=str(e)
            )
            raise

    async def save(self, user: User) -> User:
        """Persist *user* instance and commit the transaction."""
        self.__audit.info(
            "user_repository_save_started", user_id=str(user.id) if user.id else None
        )

        try:
            async with self.__database.get_session() as session:
                session.add(user)
                try:
                    await session.commit()
                except (
                    IntegrityError
                ) as e:  # safeguard against race-condition duplicates
                    self.__audit.error(
                        "user_repository_save_integrity_error",
                        user_id=str(user.id) if user.id else None,
                        error=str(e),
                    )
                    await session.rollback()
                    raise

                await session.refresh(user)

                self.__audit.info("user_repository_save_success", user_id=str(user.id))
                return user
        except Exception as e:
            self.__audit.error(
                "user_repository_save_failed",
                user_id=str(user.id) if user.id else None,
                error=str(e),
            )
            raise

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
        self.__audit.info(
            "user_repository_update_started",
            user_id=str(user.id),
            fields=list(kwargs.keys()),
        )

        try:
            async with self.__database.get_session() as session:
                # Merge the user into this session
                user = await session.merge(user)

                for field, value in kwargs.items():
                    if hasattr(user, field):
                        setattr(user, field, value)

                try:
                    await session.commit()
                except IntegrityError as e:
                    self.__audit.error(
                        "user_repository_update_integrity_error",
                        user_id=str(user.id),
                        error=str(e),
                    )
                    await session.rollback()
                    raise

                await session.refresh(user)

                self.__audit.info(
                    "user_repository_update_success", user_id=str(user.id)
                )
                return user
        except Exception as e:
            self.__audit.error(
                "user_repository_update_failed", user_id=str(user.id), error=str(e)
            )
            raise

    async def delete(self, user: User) -> None:
        """Delete *user* from the database and commit."""
        self.__audit.info("user_repository_delete_started", user_id=str(user.id))

        try:
            async with self.__database.get_session() as session:
                # Delete related refresh tokens first
                await session.execute(  # type: ignore[arg-type]
                    delete(RefreshToken).where(RefreshToken.user_id == user.id)
                )

                # Merge user into this session and delete
                user = await session.merge(user)
                await session.delete(user)
                await session.commit()

                self.__audit.info(
                    "user_repository_delete_success", user_id=str(user.id)
                )
        except Exception as e:
            self.__audit.error(
                "user_repository_delete_failed", user_id=str(user.id), error=str(e)
            )
            raise
