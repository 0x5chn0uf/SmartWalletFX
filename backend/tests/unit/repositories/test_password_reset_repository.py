from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.repositories.password_reset_repository import PasswordResetRepository


@pytest.mark.asyncio
async def test_password_reset_repository_crud(
    password_reset_repository_with_real_db, test_user
):
    token = f"tok123_{uuid.uuid4().hex[:8]}"  # Use unique token to avoid duplicates
    user_id = test_user.id  # Use real user ID instead of random UUID
    expires = datetime.now(timezone.utc) + timedelta(minutes=30)

    pr = await password_reset_repository_with_real_db.create(token, user_id, expires)
    assert pr.id

    fetched = await password_reset_repository_with_real_db.get_valid(token)
    assert fetched is not None

    await password_reset_repository_with_real_db.mark_used(fetched)
    assert fetched.used is True

    deleted = await password_reset_repository_with_real_db.delete_expired()
    assert isinstance(deleted, int)
