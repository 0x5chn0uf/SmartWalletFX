from __future__ import annotations

from datetime import datetime, timedelta, timezone
import uuid

import pytest

from app.repositories.password_reset_repository import PasswordResetRepository


@pytest.mark.asyncio
async def test_password_reset_repository_crud(db_session):
    repo = PasswordResetRepository(db_session)
    token = "tok123"
    user_id = uuid.uuid4()
    expires = datetime.now(timezone.utc) + timedelta(minutes=30)

    pr = await repo.create(token, user_id, expires)
    assert pr.id

    fetched = await repo.get_valid(token)
    assert fetched is not None

    await repo.mark_used(fetched)
    assert fetched.used is True

    deleted = await repo.delete_expired()
    assert isinstance(deleted, int)
