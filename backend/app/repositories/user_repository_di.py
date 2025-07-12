from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.services import DatabaseService
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.utils.logging import Audit


class UserRepositoryDI:
    """Repository using :class:`DatabaseService` for session management."""

    def __init__(self, db_service: DatabaseService, audit: Audit):
        self.__db_service = db_service
        self.__audit = audit

    async def get_all(self) -> list[User]:
        async with self.__db_service.get_session() as session:
            result = await session.execute(select(User))
            return result.scalars().all()

    async def get_by_username(self, username: str) -> Optional[User]:
        async with self.__db_service.get_session() as session:
            result = await session.execute(select(User).filter_by(username=username))
            return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        async with self.__db_service.get_session() as session:
            result = await session.execute(select(User).filter_by(email=email))
            return result.scalar_one_or_none()

    async def exists(self, *, username: str | None = None, email: str | None = None) -> bool:
        async with self.__db_service.get_session() as session:
            stmt = select(User.id)
            if username is not None:
                stmt = stmt.filter_by(username=username)
            if email is not None:
                stmt = stmt.filter_by(email=email)
            result = await session.execute(stmt.limit(1))
            return result.scalar_one_or_none() is not None

    async def get_by_id(self, user_id: str | uuid.UUID) -> Optional[User]:
        if isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except ValueError:
                pass
        async with self.__db_service.get_session() as session:
            return await session.get(User, user_id)

    async def save(self, user: User) -> User:
        async with self.__db_service.get_session() as session:
            session.add(user)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                raise
            await session.refresh(user)
            return user

    async def update(self, user: User, **kwargs) -> User:
        for field, value in kwargs.items():
            if hasattr(user, field):
                setattr(user, field, value)
        async with self.__db_service.get_session() as session:
            try:
                merged = await session.merge(user)
                await session.commit()
            except IntegrityError:
                await session.rollback()
                raise
            await session.refresh(merged)
            return merged

    async def delete(self, user: User) -> None:
        async with self.__db_service.get_session() as session:
            await session.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))
            await session.delete(user)
            await session.commit()
