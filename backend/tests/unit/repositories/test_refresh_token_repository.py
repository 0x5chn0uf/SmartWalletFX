from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.repositories.refresh_token_repository import RefreshTokenRepository


@pytest.mark.asyncio
async def test_refresh_token_repository_full_crud(
    refresh_token_repository_with_real_db, db_session, test_user
):
    """End-to-end coverage of create, read, revoke & delete_expired helpers."""
    user_id = test_user.id  # Use real user ID instead of random UUID

    # Create & persist new refresh token (hashed JTI)
    token = await refresh_token_repository_with_real_db.create_from_jti(
        "dummy-jti", user_id, ttl=timedelta(hours=1)
    )
    assert token.user_id == user_id
    assert token.revoked is False

    # Fetch by hashed jti
    fetched = await refresh_token_repository_with_real_db.get_by_jti_hash(
        token.jti_hash
    )
    assert fetched is not None and fetched.id == token.id

    # Revoke token & ensure flag is persisted
    await refresh_token_repository_with_real_db.revoke(fetched)
    assert fetched.revoked is True

    # Nothing should be deleted yet because token has not expired
    deleted_count = await refresh_token_repository_with_real_db.delete_expired()
    assert deleted_count == 0

    # Expire the token manually and ensure deletion happens
    fetched.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    await db_session.commit()  # Commit the expiration change

    deleted_count = await refresh_token_repository_with_real_db.delete_expired()
    assert deleted_count == 1
