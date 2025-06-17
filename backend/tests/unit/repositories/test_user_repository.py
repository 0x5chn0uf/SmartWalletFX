from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.repositories.user_repository import UserRepository


@pytest.mark.asyncio
async def test_user_repository_crud_and_exists(db_session):
    """Full happy-path coverage for save, get_* and exists helpers."""
    repo = UserRepository(db_session)

    # Save a new user
    user = User(username="alice", email="alice@example.com")
    saved = await repo.save(user)

    assert saved.id is not None

    # Fetch by username / email
    by_username = await repo.get_by_username("alice")
    by_email = await repo.get_by_email("alice@example.com")
    assert by_username is saved
    assert by_email is saved

    # exists helper (positive cases)
    assert await repo.exists(username="alice") is True
    assert await repo.exists(email="alice@example.com") is True

    # Negative case – non-existing
    assert await repo.exists(username="bob") is False
    assert await repo.get_by_username("bob") is None


@pytest.mark.asyncio
async def test_user_repository_save_integrity_error(monkeypatch):
    """save should rollback the transaction and propagate IntegrityError."""

    class DummySession:  # noqa: D101 – minimal async session stub
        def __init__(self):
            self.add_called = False
            self.rollback_called = False
            self.refresh_called = False

        # SQLAlchemy's "add" is sync
        def add(self, obj):
            self.add_called = True

        async def commit(self):
            raise IntegrityError("duplicate", None, None)

        async def rollback(self):
            self.rollback_called = True

        async def refresh(self, obj):
            self.refresh_called = True

    dummy_session = DummySession()
    repo = UserRepository(dummy_session)  # type: ignore[arg-type]

    with pytest.raises(IntegrityError):
        await repo.save(SimpleNamespace())  # user object not inspected by repo

    assert dummy_session.add_called is True
    assert dummy_session.rollback_called is True
    # refresh should *not* be called because commit failed
    assert dummy_session.refresh_called is False
