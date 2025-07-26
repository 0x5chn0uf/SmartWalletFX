from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.future import select

from app.core.database import CoreDatabase
from app.domain.interfaces.repositories import OAuthAccountRepositoryInterface
from app.models.oauth_account import OAuthAccount
from app.utils.logging import Audit


class OAuthAccountRepository(OAuthAccountRepositoryInterface):
    """Repository for :class:`OAuthAccount` entities."""

    def __init__(self, database: CoreDatabase, audit: Audit):
        self.__database = database
        self.__audit = audit

    async def get_by_provider_account(
        self, provider: str, account_id: str
    ) -> Optional[OAuthAccount]:
        """Get OAuth account by provider and account ID."""
        self.__audit.info(
            "oauth_account_repository_get_by_provider_account_started",
            provider=provider,
            account_id=account_id,
        )

        try:
            async with self.__database.get_session() as session:
                stmt = select(OAuthAccount).filter_by(
                    provider=provider, provider_account_id=account_id
                )
                result = await session.execute(stmt)
                account = result.scalar_one_or_none()

                self.__audit.info(
                    "oauth_account_repository_get_by_provider_account_success",
                    provider=provider,
                    account_id=account_id,
                    found=account is not None,
                )
                return account
        except Exception as e:
            self.__audit.error(
                "oauth_account_repository_get_by_provider_account_failed",
                provider=provider,
                account_id=account_id,
                error=str(e),
            )
            raise

    async def get_by_user_provider(
        self, user_id: uuid.UUID, provider: str
    ) -> Optional[OAuthAccount]:
        """Get OAuth account by user ID and provider."""
        self.__audit.info(
            "oauth_account_repository_get_by_user_provider_started",
            user_id=str(user_id),
            provider=provider,
        )

        try:
            async with self.__database.get_session() as session:
                stmt = select(OAuthAccount).filter_by(
                    user_id=user_id, provider=provider
                )
                result = await session.execute(stmt)
                account = result.scalar_one_or_none()

                self.__audit.info(
                    "oauth_account_repository_get_by_user_provider_success",
                    user_id=str(user_id),
                    provider=provider,
                    found=account is not None,
                )
                return account
        except Exception as e:
            self.__audit.error(
                "oauth_account_repository_get_by_user_provider_failed",
                user_id=str(user_id),
                provider=provider,
                error=str(e),
            )
            raise

    async def link_account(
        self,
        user_id: uuid.UUID,
        provider: str,
        account_id: str,
        email: str | None = None,
    ) -> OAuthAccount:
        """Link an OAuth account to a user."""
        self.__audit.info(
            "oauth_account_repository_link_account_started",
            user_id=str(user_id),
            provider=provider,
            account_id=account_id,
        )

        try:
            async with self.__database.get_session() as session:
                account = OAuthAccount(
                    user_id=user_id,
                    provider=provider,
                    provider_account_id=account_id,
                    email=email,
                )
                session.add(account)
                await session.commit()
                await session.refresh(account)

                self.__audit.info(
                    "oauth_account_repository_link_account_success",
                    user_id=str(user_id),
                    provider=provider,
                    account_id=account_id,
                )
                return account
        except Exception as e:
            self.__audit.error(
                "oauth_account_repository_link_account_failed",
                user_id=str(user_id),
                provider=provider,
                account_id=account_id,
                error=str(e),
            )
            raise
