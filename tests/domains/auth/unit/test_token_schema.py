import pytest

from app.domain.schemas.auth_token import TokenResponse


@pytest.mark.unit
def test_token_response_defaults():
    resp = TokenResponse(
        access_token="access.jwt",
        expires_in=900,
        refresh_token="refresh.jwt",
    )
    assert resp.token_type == "bearer"
    assert resp.access_token == "access.jwt"
    assert resp.refresh_token == "refresh.jwt"
    assert resp.expires_in == 900


@pytest.mark.unit
def test_token_response_validation_errors():
    """Missing required fields should raise validation error."""
    with pytest.raises(Exception):
        TokenResponse(access_token="x", expires_in=60)  # missing refresh_token
