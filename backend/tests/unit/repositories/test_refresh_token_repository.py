from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.repositories.refresh_token_repository import RefreshTokenRepository


@pytest.mark.asyncio
async def test_refresh_token_repository_full_crud(db_session):
    """End-to-end coverage of create, read, revoke & delete_expired helpers."""

    repo = RefreshTokenRepository(db_session)
    user_id = uuid.uuid4()

    # Create & persist new refresh token (hashed JTI)
    token = await repo.create_from_jti("dummy-jti", user_id, ttl=timedelta(hours=1))
    assert token.user_id == user_id
    assert token.revoked is False

    # Fetch by hashed jti
    fetched = await repo.get_by_jti_hash(token.jti_hash)
    assert fetched is not None and fetched.id == token.id

    # Revoke token & ensure flag is persisted
    await repo.revoke(fetched)
    assert fetched.revoked is True

    # Nothing should be deleted yet because token has not expired
    deleted_count = await repo.delete_expired()
    assert deleted_count == 0

    # Expire the token manually and ensure deletion happens
    fetched.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    await db_session.commit()

    deleted_count = await repo.delete_expired()
    assert deleted_count == 1
