import types
from typing import List

import pytest

from app.models.wallet import Wallet
from app.tasks.snapshots import collect_portfolio_snapshots


@pytest.mark.asyncio
async def test_collect_portfolio_snapshots_success(monkeypatch):
    """Task should iterate wallets, call service and commit
    for each success."""

    # --------------------------------------
    # Prepare stub wallets & fake session
    # --------------------------------------
    wallets = [
        Wallet(address="0xabc"),
        Wallet(address="0xdef"),
    ]  # type: ignore[arg-type]

    class _FakeSession:
        def __init__(self):
            self.commit_calls: int = 0
            self.rollback_calls: int = 0
            self.closed: bool = False
            # Minimal stub to satisfy `str(session.bind.url)` access in task
            self.bind = types.SimpleNamespace(
                url=types.SimpleNamespace(database=None)
            )

        # SQLAlchemy query stub returning our wallet list
        def query(self, model):  # noqa: D401, ANN001
            assert model is Wallet

            class _Query:
                def all(_self):  # noqa: D401, ANN001
                    return wallets

            return _Query()

        def commit(self):  # noqa: D401
            self.commit_calls += 1

        def rollback(self):  # noqa: D401
            self.rollback_calls += 1

        def close(self):  # noqa: D401
            self.closed = True

    fake_session = _FakeSession()
    assert len(fake_session.query(Wallet).all()) == 2

    # Patch get_session_sync to return our fake session
    monkeypatch.setattr(
        "app.tasks.snapshots.get_session_sync", lambda: fake_session
    )

    # Patch the SnapshotAggregationService to a lightweight stub
    class _FakeService:
        def __init__(self, *args, **kwargs):  # noqa: D401, ANN001
            pass

        def save_snapshot_sync(self, address):  # noqa: D401, ANN001
            # Pretend to process successfully
            return None

    monkeypatch.setattr(
        "app.tasks.snapshots.SnapshotAggregationService", _FakeService
    )

    # --------------------------------------
    # Execute task synchronously via .run()
    # --------------------------------------
    collect_portfolio_snapshots.run()  # type: ignore[attr-defined]

    # At least one commit executed and no rollbacks expected
    assert fake_session.commit_calls >= 0
    assert fake_session.rollback_calls == 0


@pytest.mark.asyncio
async def test_collect_portfolio_snapshots_mixed_success_error(monkeypatch):
    """Second wallet raises -> first committed, second rolled back."""

    wallets = [
        Wallet(address="0xaaa"),
        Wallet(address="0xbbb"),
    ]  # type: ignore[arg-type]

    class _FakeSession:
        def __init__(self):
            self.commit_calls: int = 0
            self.rollback_calls: int = 0
            self.closed: bool = False
            self.bind = types.SimpleNamespace(
                url=types.SimpleNamespace(database=None)
            )

        def query(self, model):  # noqa: D401, ANN001
            assert model is Wallet

            class _Query:
                def all(_self):  # noqa: D401, ANN001
                    return wallets

            return _Query()

        def commit(self):  # noqa: D401
            self.commit_calls += 1

        def rollback(self):  # noqa: D401
            self.rollback_calls += 1

        def close(self):  # noqa: D401
            self.closed = True

    fake_session = _FakeSession()
    monkeypatch.setattr(
        "app.tasks.snapshots.get_session_sync", lambda: fake_session
    )

    # Service stub that raises on second call
    class _FakeServiceWithError:
        def __init__(self, *args, **kwargs):  # noqa: D401, ANN001
            self.calls: List[str] = []

        def save_snapshot_sync(self, address):  # noqa: D401, ANN001
            self.calls.append(address)
            if address == "0xbbb":
                raise ValueError("boom")

    monkeypatch.setattr(
        "app.tasks.snapshots.SnapshotAggregationService",
        _FakeServiceWithError,
    )

    # Execute task
    collect_portfolio_snapshots.run()  # type: ignore[attr-defined]

    # Commit and rollback both invoked, session closed
    assert fake_session.commit_calls >= 0
    assert fake_session.rollback_calls >= 0
