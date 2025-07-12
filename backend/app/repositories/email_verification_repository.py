from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.email_verification import EmailVerification
from app.utils.logging import Audit


class EmailVerificationRepository:
    """Repository for email verification tokens."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self, token: str, user_id: uuid.UUID, expires_at: datetime
    ) -> EmailVerification:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        ev = EmailVerification(
            token_hash=token_hash, user_id=user_id, expires_at=expires_at
        )
        self._session.add(ev)
        await self._session.commit()
        await self._session.refresh(ev)
        Audit.info("email_verification_token_created", user_id=str(user_id))
        return ev

    async def get_valid(self, token: str) -> Optional[EmailVerification]:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        stmt = select(EmailVerification).where(
            EmailVerification.token_hash == token_hash,
            EmailVerification.expires_at > datetime.now(timezone.utc),
            EmailVerification.used.is_(False),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_used(self, ev: EmailVerification) -> None:
        ev.used = True
        await self._session.commit()
        Audit.info("email_verification_token_used", token_hash=ev.token_hash)

    async def delete_expired(self) -> int:
        stmt = EmailVerification.__table__.delete().where(
            EmailVerification.expires_at < datetime.now(timezone.utc)
        )
        result = await self._session.execute(stmt)
        await self._session.commit()
        Audit.info("email_verification_tokens_deleted", count=result.rowcount)
        return result.rowcount
