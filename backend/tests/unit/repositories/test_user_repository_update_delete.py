import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.user_repository import UserRepository


@pytest.mark.asyncio
async def test_user_repository_update(db_session, monkeypatch):
    repo = UserRepository(db_session)

    # Create and persist original user
    user = User(
        username=f"bob-{uuid.uuid4().hex[:8]}",
        email=f"bob-{uuid.uuid4().hex[:8]}@example.com",
    )
    saved = await repo.save(user)

    # Update username only (happy-path)
    updated = await repo.update(saved, username="robert")
    assert updated.username == "robert"

    # Provide an unknown attribute – should be ignored and *not* raise
    updated = await repo.update(saved, non_existing="noop")  # type: ignore[arg-type]
    assert not hasattr(updated, "non_existing")


@pytest.mark.asyncio
async def test_user_repository_delete_cascades_refresh_tokens(db_session, monkeypatch):
    repo = UserRepository(db_session)

    user = User(
        username=f"carol-{uuid.uuid4().hex[:8]}",
        email=f"carol-{uuid.uuid4().hex[:8]}@example.com",
    )
    saved = await repo.save(user)

    # Attach a refresh token row
    rt = RefreshToken(
        jti_hash="dummy",
        user_id=saved.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db_session.add(rt)
    await db_session.commit()

    # Ensure token exists before deletion
    token_before = await db_session.get(RefreshToken, rt.id)
    assert token_before is not None

    # Delete user via helper – should also delete refresh tokens
    await repo.delete(saved)

    # Verify user gone
    assert await repo.get_by_id(saved.id) is None
    # Verify token gone
    token_after = await db_session.get(RefreshToken, rt.id)
    assert token_after is None
