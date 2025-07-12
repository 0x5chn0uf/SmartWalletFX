from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.future import select

from app.core.database import DatabaseService
from app.models.email_verification import EmailVerification
from app.utils.logging import Audit


class EmailVerificationRepository:
    """Repository for email verification tokens."""

    def __init__(self, database_service: DatabaseService, audit: Audit):
        self.__database_service = database_service
        self.__audit = audit

    async def create(
        self, token: str, user_id: uuid.UUID, expires_at: datetime
    ) -> EmailVerification:
        """Create a new email verification token."""
        self.__audit.info(
            "email_verification_repository_create_started", user_id=str(user_id)
        )

        try:
            async with self.__database_service.get_session() as session:
                token_hash = hashlib.sha256(token.encode()).hexdigest()
                ev = EmailVerification(
                    token_hash=token_hash, user_id=user_id, expires_at=expires_at
                )
                session.add(ev)
                await session.commit()
                await session.refresh(ev)

                self.__audit.info(
                    "email_verification_repository_create_success", user_id=str(user_id)
                )
                return ev
        except Exception as e:
            self.__audit.error(
                "email_verification_repository_create_failed",
                user_id=str(user_id),
                error=str(e),
            )
            raise

    async def get_valid(self, token: str) -> Optional[EmailVerification]:
        """Get a valid (unexpired, unused) email verification token."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        self.__audit.info(
            "email_verification_repository_get_valid_started", token_hash=token_hash[:8]
        )

        try:
            async with self.__database_service.get_session() as session:
                stmt = select(EmailVerification).where(
                    EmailVerification.token_hash == token_hash,
                    EmailVerification.expires_at > datetime.now(timezone.utc),
                    EmailVerification.used.is_(False),
                )
                result = await session.execute(stmt)
                ev = result.scalar_one_or_none()

                self.__audit.info(
                    "email_verification_repository_get_valid_success",
                    token_hash=token_hash[:8],
                    found=ev is not None,
                )
                return ev
        except Exception as e:
            self.__audit.error(
                "email_verification_repository_get_valid_failed",
                token_hash=token_hash[:8],
                error=str(e),
            )
            raise

    async def mark_used(self, ev: EmailVerification) -> None:
        """Mark an email verification token as used."""
        self.__audit.info(
            "email_verification_repository_mark_used_started",
            token_hash=ev.token_hash[:8],
        )

        try:
            async with self.__database_service.get_session() as session:
                # Merge the object to attach it to the current session
                merged_ev = await session.merge(ev)
                merged_ev.used = True
                await session.commit()

                self.__audit.info(
                    "email_verification_repository_mark_used_success",
                    token_hash=ev.token_hash[:8],
                )
        except Exception as e:
            self.__audit.error(
                "email_verification_repository_mark_used_failed",
                token_hash=ev.token_hash[:8],
                error=str(e),
            )
            raise

    async def delete_expired(self) -> int:
        """Delete expired email verification tokens."""
        self.__audit.info("email_verification_repository_delete_expired_started")

        try:
            async with self.__database_service.get_session() as session:
                stmt = EmailVerification.__table__.delete().where(
                    EmailVerification.expires_at < datetime.now(timezone.utc)
                )
                result = await session.execute(stmt)
                await session.commit()

                self.__audit.info(
                    "email_verification_repository_delete_expired_success",
                    count=result.rowcount,
                )
                return result.rowcount
        except Exception as e:
            self.__audit.error(
                "email_verification_repository_delete_expired_failed", error=str(e)
            )
            raise
