from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.oauth_account import OAuthAccount


class OAuthAccountRepository:
    """Repository for :class:`OAuthAccount` entities."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_provider_account(
        self, provider: str, account_id: str
    ) -> Optional[OAuthAccount]:
        stmt = select(OAuthAccount).filter_by(
            provider=provider, provider_account_id=account_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_provider(
        self, user_id: uuid.UUID, provider: str
    ) -> Optional[OAuthAccount]:
        stmt = select(OAuthAccount).filter_by(user_id=user_id, provider=provider)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def link_account(
        self,
        user_id: uuid.UUID,
        provider: str,
        account_id: str,
        email: str | None = None,
    ) -> OAuthAccount:
        account = OAuthAccount(
            user_id=user_id,
            provider=provider,
            provider_account_id=account_id,
            email=email,
        )
        self._session.add(account)
        await self._session.commit()
        await self._session.refresh(account)
        return account
