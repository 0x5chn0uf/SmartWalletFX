from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.domain.errors import InvalidCredentialsError
from app.models.user import User
from app.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_register_via_kwargs(auth_service, mock_user_repo):
    mock_user_repo.exists.return_value = False
    mock_user_repo.save.return_value = User(
        id=2, username="via", email="via@example.com"
    )

    user = await auth_service.register(email="via@example.com", password="Str0ng!pw")

    assert user.username == "via"
    assert mock_user_repo.exists.call_count == 2
    mock_user_repo.save.assert_awaited()


@pytest.mark.asyncio
async def test_register_kwargs_missing_fields(auth_service):
    with pytest.raises(ValueError):
        await auth_service.register(email="foo@example.com")


@pytest.mark.asyncio
@patch("app.services.auth_service.JWTUtils")
async def test_refresh_missing_fields(mock_jwt, auth_service):
    mock_jwt.decode_token.return_value = {"type": "refresh", "sub": "", "jti": ""}
    with pytest.raises(InvalidCredentialsError):
        await auth_service.refresh("bad")


@pytest.mark.asyncio
@patch("app.services.auth_service.RefreshTokenRepository")
@patch("app.services.auth_service.JWTUtils")
async def test_revoke_refresh_token_valid(mock_jwt, mock_repo_cls, auth_service):
    mock_jwt.decode_token.return_value = {"sub": "1", "jti": "tok"}
    mock_repo = AsyncMock()
    mock_repo_cls.return_value = mock_repo
    token_obj = Mock(revoked=False)
    mock_repo.get_by_jti_hash.return_value = token_obj

    await auth_service.revoke_refresh_token("valid")

    mock_repo.revoke.assert_awaited_with(token_obj)


@pytest.mark.asyncio
@patch("app.services.auth_service.JWTUtils")
async def test_revoke_refresh_token_invalid(mock_jwt, auth_service, mock_user_repo):
    mock_jwt.decode_token.side_effect = Exception("bad")
    await auth_service.revoke_refresh_token("boom")
    mock_user_repo._session.assert_not_called()
