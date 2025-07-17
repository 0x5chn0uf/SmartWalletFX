from __future__ import annotations

from datetime import timedelta
from typing import Optional

from jose import jwt as jose_jwt

from app.core.config import ConfigurationService
from app.core.security.roles import UserRole
from app.domain.schemas.auth_token import TokenResponse
from app.models.user import User
from app.repositories.oauth_account_repository import OAuthAccountRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.utils.jwt import JWTUtils
from app.utils.logging import Audit


class OAuthService:
    """Handle OAuth-based authentication and account linking."""

    def __init__(
        self,
        user_repo: UserRepository,
        oauth_account_repo: OAuthAccountRepository,
        refresh_token_repo: RefreshTokenRepository,
        jwt_utils: JWTUtils,
        config_service: ConfigurationService,
        audit: Audit,
    ):
        self.__user_repo = user_repo
        self.__oauth_account_repo = oauth_account_repo
        self.__refresh_token_repo = refresh_token_repo
        self.__jwt_utils = jwt_utils
        self.__config_service = config_service
        self.__audit = audit

    async def authenticate_or_create(
        self, provider: str, account_id: str, email: Optional[str]
    ) -> User:
        account = await self.__oauth_account_repo.get_by_provider_account(
            provider, account_id
        )
        if account:
            user = await self.__user_repo.get_by_id(account.user_id)
            if user is None:
                self.__audit.error(
                    "oauth_link_missing_user", provider=provider, account_id=account_id
                )
                raise ValueError("Linked user missing")
            self.__audit.info(
                "oauth_existing_account", provider=provider, user_id=str(user.id)
            )
            return user

        user = None
        if email:
            user = await self.__user_repo.get_by_email(email)

        if user is None:
            username = (email or account_id).split("@")[0]
            user = User(
                username=username,
                email=email or f"{account_id}@{provider}",
                roles=[UserRole.INDIVIDUAL_INVESTOR.value],
                attributes={},
            )
            user = await self.__user_repo.save(user)
            self.__audit.info(
                "oauth_user_created", provider=provider, user_id=str(user.id)
            )

        await self.__oauth_account_repo.link_account(
            user.id, provider, account_id, email
        )
        self.__audit.info(
            "oauth_account_linked", provider=provider, user_id=str(user.id)
        )
        return user

    async def issue_tokens(self, user: User) -> TokenResponse:
        roles = user.roles or [UserRole.INDIVIDUAL_INVESTOR.value]
        attrs = user.attributes or {}

        access_token = self.__jwt_utils.create_access_token(
            str(user.id), additional_claims={"roles": roles, "attributes": attrs}
        )
        refresh_token = self.__jwt_utils.create_refresh_token(str(user.id))

        payload = jose_jwt.get_unverified_claims(refresh_token)
        jti = payload["jti"]
        ttl = timedelta(days=self.__config_service.REFRESH_TOKEN_EXPIRE_DAYS)

        await self.__refresh_token_repo.create_from_jti(jti, user.id, ttl)
        self.__audit.info("oauth_tokens_issued", user_id=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.__config_service.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
