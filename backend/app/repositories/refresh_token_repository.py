"""Repository layer for :class:`app.models.refresh_token.RefreshToken`."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.future import select

from app.core.database import CoreDatabase
from app.models.refresh_token import RefreshToken
from app.utils.logging import Audit


class RefreshTokenRepository:
    """Async repository handling refresh token persistence & queries."""

    def __init__(self, database: CoreDatabase, audit: Audit):
        self.__database = database
        self.__audit = audit

    async def save(self, token: RefreshToken) -> RefreshToken:
        """Save a refresh token to the database."""
        self.__audit.info(
            "refresh_token_repository_save_started",
            user_id=str(token.user_id),
            jti_hash=token.jti_hash[:8],
        )

        try:
            async with self.__database.get_session() as session:
                session.add(token)
                await session.commit()
                await session.refresh(token)

                self.__audit.info(
                    "refresh_token_repository_save_success",
                    user_id=str(token.user_id),
                    jti_hash=token.jti_hash[:8],
                )
                return token
        except Exception as e:
            self.__audit.error(
                "refresh_token_repository_save_failed",
                user_id=str(token.user_id),
                jti_hash=token.jti_hash[:8],
                error=str(e),
            )
            raise

    async def get_by_jti_hash(self, jti_hash: str) -> Optional[RefreshToken]:
        """Get a refresh token by JTI hash."""
        self.__audit.info(
            "refresh_token_repository_get_by_jti_hash_started", jti_hash=jti_hash[:8]
        )

        try:
            async with self.__database.get_session() as session:
                stmt = select(RefreshToken).filter_by(jti_hash=jti_hash)
                result = await session.execute(stmt)
                token = result.scalar_one_or_none()

                self.__audit.info(
                    "refresh_token_repository_get_by_jti_hash_success",
                    jti_hash=jti_hash[:8],
                    found=token is not None,
                )
                return token
        except Exception as e:
            self.__audit.error(
                "refresh_token_repository_get_by_jti_hash_failed",
                jti_hash=jti_hash[:8],
                error=str(e),
            )
            raise

    async def revoke(self, token: RefreshToken) -> None:
        """Revoke a refresh token."""
        self.__audit.info(
            "refresh_token_repository_revoke_started",
            user_id=str(token.user_id),
            jti_hash=token.jti_hash[:8],
        )

        try:
            async with self.__database.get_session() as session:
                # Merge the object to attach it to the current session
                merged_token = await session.merge(token)
                merged_token.revoked = True
                await session.commit()

                self.__audit.info(
                    "refresh_token_repository_revoke_success",
                    user_id=str(token.user_id),
                    jti_hash=token.jti_hash[:8],
                )
        except Exception as e:
            self.__audit.error(
                "refresh_token_repository_revoke_failed",
                user_id=str(token.user_id),
                jti_hash=token.jti_hash[:8],
                error=str(e),
            )
            raise

    async def delete_expired(self, *, before: datetime | None = None) -> int:
        """Delete tokens expired before *before* (default: now). Returns rowcount."""
        cutoff = before or datetime.now(timezone.utc)
        self.__audit.info(
            "refresh_token_repository_delete_expired_started", cutoff=cutoff.isoformat()
        )

        try:
            async with self.__database.get_session() as session:
                stmt = RefreshToken.__table__.delete().where(
                    RefreshToken.expires_at < cutoff
                )
                result = await session.execute(stmt)
                await session.commit()

                self.__audit.info(
                    "refresh_token_repository_delete_expired_success",
                    count=result.rowcount,
                    cutoff=cutoff.isoformat(),
                )
                return result.rowcount
        except Exception as e:
            self.__audit.error(
                "refresh_token_repository_delete_expired_failed",
                cutoff=cutoff.isoformat(),
                error=str(e),
            )
            raise

    async def create_from_jti(
        self, jti: str, user_id: uuid.UUID, ttl: timedelta
    ) -> RefreshToken:
        """Create a refresh token from JTI."""
        self.__audit.info(
            "refresh_token_repository_create_from_jti_started",
            user_id=str(user_id),
            ttl_seconds=ttl.total_seconds(),
        )

        try:
            token = RefreshToken.from_raw_jti(jti, user_id, ttl)
            saved_token = await self.save(token)

            self.__audit.info(
                "refresh_token_repository_create_from_jti_success",
                user_id=str(user_id),
                jti_hash=saved_token.jti_hash[:8],
            )
            return saved_token
        except Exception as e:
            self.__audit.error(
                "refresh_token_repository_create_from_jti_failed",
                user_id=str(user_id),
                error=str(e),
            )
            raise
