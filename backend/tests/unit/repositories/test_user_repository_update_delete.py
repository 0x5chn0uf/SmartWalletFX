import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.user_repository import UserRepository

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _disable_audit_listener(monkeypatch):  # noqa: D401 – helper not a public API
    """Disable the *after_flush* audit hook for this test.

    The default hook tries to insert :class:`app.models.audit_log.AuditLog` rows
    that rely on the Postgres-only ``timezone('utc', now())`` function. When
    the suite runs under SQLite that function is missing and the INSERT fails
    with ``OperationalError: unknown function: timezone``.

    We therefore *unregister* the hook completely and override the symbol with
    a no-op to prevent any re-registration attempts during the current test.
    """

    from sqlalchemy import event as _sa_event
    from sqlalchemy.orm import Session

    import app.utils.audit as audit_utils  # local import to avoid early side-effects

    # Remove the listener if it's registered. SQLAlchemy matches by *object
    # identity*, so we must pass the original function object.
    try:
        _sa_event.remove(Session, "after_flush", audit_utils.on_after_flush)  # type: ignore[arg-type]
    except Exception:
        # Listener was already removed or never registered – that's fine.
        pass

    # Monkey-patch the attribute to a harmless lambda so that even if some code
    # re-attaches it later, it will do nothing.
    monkeypatch.setattr(
        audit_utils,
        "on_after_flush",
        lambda *args, **kwargs: None,
    )


@pytest.mark.asyncio
async def test_user_repository_update(db_session, monkeypatch):
    _disable_audit_listener(monkeypatch)

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
    _disable_audit_listener(monkeypatch)

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
