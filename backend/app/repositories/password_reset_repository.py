from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.future import select

from app.core.database import DatabaseService
from app.models.password_reset import PasswordReset
from app.utils.logging import Audit


class PasswordResetRepository:
    """Repository for password reset tokens."""

    def __init__(self, database_service: DatabaseService, audit: Audit):
        self.__database_service = database_service
        self.__audit = audit

    async def create(
        self, token: str, user_id: uuid.UUID, expires_at: datetime
    ) -> PasswordReset:
        """Create a new password reset token."""
        self.__audit.info(
            "password_reset_repository_create_started", user_id=str(user_id)
        )

        try:
            async with self.__database_service.get_session() as session:
                token_hash = hashlib.sha256(token.encode()).hexdigest()
                pr = PasswordReset(
                    token_hash=token_hash, user_id=user_id, expires_at=expires_at
                )
                session.add(pr)
                await session.commit()
                await session.refresh(pr)

                self.__audit.info(
                    "password_reset_repository_create_success", user_id=str(user_id)
                )
                return pr
        except Exception as e:
            self.__audit.error(
                "password_reset_repository_create_failed",
                user_id=str(user_id),
                error=str(e),
            )
            raise

    async def get_valid(self, token: str) -> Optional[PasswordReset]:
        """Get a valid (unexpired, unused) password reset token."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        self.__audit.info(
            "password_reset_repository_get_valid_started", token_hash=token_hash[:8]
        )

        try:
            async with self.__database_service.get_session() as session:
                stmt = select(PasswordReset).where(
                    PasswordReset.token_hash == token_hash,
                    PasswordReset.expires_at > datetime.now(timezone.utc),
                    PasswordReset.used.is_(False),
                )
                result = await session.execute(stmt)
                pr = result.scalar_one_or_none()

                self.__audit.info(
                    "password_reset_repository_get_valid_success",
                    token_hash=token_hash[:8],
                    found=pr is not None,
                )
                return pr
        except Exception as e:
            self.__audit.error(
                "password_reset_repository_get_valid_failed",
                token_hash=token_hash[:8],
                error=str(e),
            )
            raise

    async def mark_used(self, pr: PasswordReset) -> None:
        """Mark a password reset token as used."""
        self.__audit.info(
            "password_reset_repository_mark_used_started",
            token_hash=pr.token_hash[:8],
        )

        try:
            async with self.__database_service.get_session() as session:
                # Merge the object to attach it to the current session
                merged_pr = await session.merge(pr)
                merged_pr.used = True
                await session.commit()

                self.__audit.info(
                    "password_reset_repository_mark_used_success",
                    token_hash=pr.token_hash[:8],
                )
        except Exception as e:
            self.__audit.error(
                "password_reset_repository_mark_used_failed",
                token_hash=pr.token_hash[:8],
                error=str(e),
            )
            raise

    async def delete_expired(self) -> int:
        """Delete expired password reset tokens."""
        self.__audit.info("password_reset_repository_delete_expired_started")

        try:
            async with self.__database_service.get_session() as session:
                stmt = PasswordReset.__table__.delete().where(
                    PasswordReset.expires_at < datetime.now(timezone.utc)
                )
                result = await session.execute(stmt)
                await session.commit()

                self.__audit.info(
                    "password_reset_repository_delete_expired_success",
                    count=result.rowcount,
                )
                return result.rowcount
        except Exception as e:
            self.__audit.error(
                "password_reset_repository_delete_expired_failed", error=str(e)
            )
            raise
