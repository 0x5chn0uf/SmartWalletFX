from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.password_reset import PasswordReset


class PasswordResetRepository:
    """Repository for password reset tokens."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, token: str, user_id: uuid.UUID, expires_at: datetime) -> PasswordReset:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        pr = PasswordReset(token_hash=token_hash, user_id=user_id, expires_at=expires_at)
        self._session.add(pr)
        await self._session.commit()
        await self._session.refresh(pr)
        return pr

    async def get_valid(self, token: str) -> Optional[PasswordReset]:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        stmt = select(PasswordReset).where(
            PasswordReset.token_hash == token_hash,
            PasswordReset.expires_at > datetime.now(timezone.utc),
            PasswordReset.used.is_(False),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_used(self, pr: PasswordReset) -> None:
        pr.used = True
        await self._session.commit()

    async def delete_expired(self) -> int:
        stmt = PasswordReset.__table__.delete().where(
            PasswordReset.expires_at < datetime.now(timezone.utc)
        )
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount
