from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.repositories.email_verification_repository import EmailVerificationRepository


@pytest.mark.asyncio
async def test_email_verification_repository_crud(db_session):
    repo = EmailVerificationRepository(db_session)
    token = "tok123"
    user_id = uuid.uuid4()
    expires = datetime.now(timezone.utc) + timedelta(minutes=30)

    ev = await repo.create(token, user_id, expires)
    assert ev.id

    fetched = await repo.get_valid(token)
    assert fetched is not None

    await repo.mark_used(fetched)
    assert fetched.used is True

    deleted = await repo.delete_expired()
    assert isinstance(deleted, int)
