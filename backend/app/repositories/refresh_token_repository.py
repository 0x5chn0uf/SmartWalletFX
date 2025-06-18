from __future__ import annotations

"""Repository layer for :class:`app.models.refresh_token.RefreshToken`."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    """Async repository handling refresh token persistence & queries."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, token: RefreshToken) -> RefreshToken:
        self._session.add(token)
        await self._session.commit()
        await self._session.refresh(token)
        return token

    async def get_by_jti_hash(self, jti_hash: str) -> Optional[RefreshToken]:
        stmt = select(RefreshToken).filter_by(jti_hash=jti_hash)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke(self, token: RefreshToken) -> None:
        token.revoked = True
        await self._session.commit()

    async def delete_expired(self, *, before: datetime | None = None) -> int:
        """Delete tokens expired before *before* (default: now). Returns rowcount."""

        cutoff = before or datetime.now(timezone.utc)
        stmt = RefreshToken.__table__.delete().where(RefreshToken.expires_at < cutoff)
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount

    async def create_from_jti(
        self, jti: str, user_id: uuid.UUID, ttl: timedelta
    ) -> RefreshToken:
        token = RefreshToken.from_raw_jti(jti, user_id, ttl)
        return await self.save(token)
