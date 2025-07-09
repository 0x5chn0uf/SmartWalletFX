from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, Mock

import pytest

from app.models.user import User
from app.services.oauth_service import OAuthService


@pytest.mark.asyncio
async def test_authenticate_creates_user_if_missing(db_session):
    svc = OAuthService(db_session)
    svc._users = AsyncMock()
    svc._oauth = AsyncMock()

    svc._oauth.get_by_provider_account.return_value = None
    svc._users.get_by_email.return_value = None

    created_user = User(id=uuid.uuid4(), username="alice", email="alice@example.com")
    svc._users.save.return_value = created_user

    user = await svc.authenticate_or_create("google", "123", "alice@example.com")

    svc._oauth.link_account.assert_awaited_with(
        created_user.id, "google", "123", "alice@example.com"
    )
    assert user == created_user


@pytest.mark.asyncio
async def test_issue_tokens_creates_refresh_entry(db_session, monkeypatch):
    svc = OAuthService(db_session)
    user = User(
        id=uuid.uuid4(),
        username="bob",
        email="bob@example.com",
        roles=["r"],
        attributes={},
    )

    mock_rt_repo = AsyncMock()
    monkeypatch.setattr(
        "app.services.oauth_service.RefreshTokenRepository",
        lambda session: mock_rt_repo,
    )

    tokens = await svc.issue_tokens(user)

    assert tokens.access_token
    assert tokens.refresh_token
    mock_rt_repo.create_from_jti.assert_awaited()


@pytest.mark.asyncio
async def test_authenticate_existing_account(db_session):
    svc = OAuthService(db_session)
    svc._users = AsyncMock()
    svc._oauth = AsyncMock()
    account = Mock(user_id=uuid.uuid4())
    svc._oauth.get_by_provider_account.return_value = account
    existing_user = User(id=account.user_id, username="ex", email="ex@example.com")
    svc._users.get_by_id.return_value = existing_user

    user = await svc.authenticate_or_create("github", "id123", "ex@example.com")

    assert user == existing_user
    svc._users.get_by_id.assert_awaited_with(account.user_id)


@pytest.mark.asyncio
async def test_authenticate_link_missing_user(db_session):
    svc = OAuthService(db_session)
    svc._users = AsyncMock()
    svc._oauth = AsyncMock()
    account = Mock(user_id=uuid.uuid4())
    svc._oauth.get_by_provider_account.return_value = account
    svc._users.get_by_id.return_value = None

    with pytest.raises(ValueError):
        await svc.authenticate_or_create("github", "id123", None)
    svc._users.get_by_id.assert_awaited_with(account.user_id)
