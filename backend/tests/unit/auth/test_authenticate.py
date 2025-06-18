import pytest

from app.schemas.user import UserCreate
from app.services.auth_service import AuthService


@pytest.mark.anyio
async def test_authenticate_success(db_session):
    """A user can obtain tokens with correct credentials (TDD stub)."""

    service = AuthService(db_session)

    # Arrange – register a user first
    payload = UserCreate(
        username="eve", email="eve@example.com", password="Str0ng!pwd1"
    )
    await service.register(payload)

    # Act – attempt to authenticate – expecting TokenResponse (will fail)
    token_response = await service.authenticate("eve", "Str0ng!pwd1")  # noqa: F841

    # Assert – check if the token response is as expected
    assert token_response is not None
    assert token_response.access_token is not None
    assert token_response.refresh_token is not None
