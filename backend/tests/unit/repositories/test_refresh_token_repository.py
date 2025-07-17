from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.repositories.refresh_token_repository import RefreshTokenRepository


@pytest.mark.asyncio
async def test_refresh_token_repository_create_from_jti(
    refresh_token_repository_with_di
):
    """Test create_from_jti method."""
    user_id = uuid.uuid4()
    jti = "dummy-jti"
    ttl = timedelta(hours=1)

    # Create token
    token = await refresh_token_repository_with_di.create_from_jti(
        jti, user_id, ttl
    )
    
    # Verify token was created with correct properties
    assert token.user_id == user_id
    assert token.jti_hash is not None
    assert len(token.jti_hash) == 64  # SHA-256 hash is 64 chars
    assert token.expires_at is not None


@pytest.mark.asyncio 
async def test_refresh_token_repository_save(
    refresh_token_repository_with_di
):
    """Test save method."""
    from app.models.refresh_token import RefreshToken
    
    user_id = uuid.uuid4()
    token = RefreshToken.from_raw_jti("test-jti", user_id, timedelta(hours=1))
    
    # Save token
    saved_token = await refresh_token_repository_with_di.save(token)
    
    # Verify token was saved (mock may not set ID, so just verify it returns a token)
    assert saved_token is not None
    assert saved_token.user_id == user_id
    assert saved_token.jti_hash is not None
