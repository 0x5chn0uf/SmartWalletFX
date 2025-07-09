from __future__ import annotations

from datetime import timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security.roles import UserRole
from app.models.user import User
from app.repositories.oauth_account_repository import OAuthAccountRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth_token import TokenResponse
from app.utils.jwt import JWTUtils
from app.utils.logging import Audit


class OAuthService:
    """Handle OAuth-based authentication and account linking."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._users = UserRepository(session)
        self._oauth = OAuthAccountRepository(session)

    async def authenticate_or_create(
        self, provider: str, account_id: str, email: Optional[str]
    ) -> User:
        account = await self._oauth.get_by_provider_account(provider, account_id)
        if account:
            user = await self._users.get_by_id(account.user_id)
            if user is None:
                Audit.error(
                    "oauth_link_missing_user", provider=provider, account_id=account_id
                )
                raise ValueError("Linked user missing")
            Audit.info(
                "oauth_existing_account", provider=provider, user_id=str(user.id)
            )
            return user

        user = None
        if email:
            user = await self._users.get_by_email(email)

        if user is None:
            username = (email or account_id).split("@")[0]
            user = User(
                username=username,
                email=email or f"{account_id}@{provider}",
                roles=[UserRole.INDIVIDUAL_INVESTOR.value],
                attributes={},
            )
            user = await self._users.save(user)
            Audit.info("oauth_user_created", provider=provider, user_id=str(user.id))

        await self._oauth.link_account(user.id, provider, account_id, email)
        Audit.info("oauth_account_linked", provider=provider, user_id=str(user.id))
        return user

    async def issue_tokens(self, user: User) -> TokenResponse:
        roles = user.roles or [UserRole.INDIVIDUAL_INVESTOR.value]
        attrs = user.attributes or {}

        access_token = JWTUtils.create_access_token(
            str(user.id), additional_claims={"roles": roles, "attributes": attrs}
        )
        refresh_token = JWTUtils.create_refresh_token(str(user.id))

        from jose import jwt as jose_jwt

        payload = jose_jwt.get_unverified_claims(refresh_token)
        jti = payload["jti"]
        ttl = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        rt_repo = RefreshTokenRepository(self._session)
        await rt_repo.create_from_jti(jti, user.id, ttl)
        Audit.info("oauth_tokens_issued", user_id=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
