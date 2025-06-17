import pytest

from app.core import init_db as init_module


class _DummyConn:
    def __init__(self, should_raise: bool = False):
        self.called_with = None
        self._should_raise = should_raise

    async def run_sync(self, fn):
        if self._should_raise:
            raise ValueError("boom")
        self.called_with = fn


class _DummyCtxMgr:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, exc_type, exc, tb):
        # swallow exceptions so they propagate (we don't handle)
        return False


class _DummyEngine:
    def __init__(self, conn):
        self._conn = conn
        self.begin_called = False

    def begin(self):
        self.begin_called = True
        return _DummyCtxMgr(self._conn)


@pytest.mark.asyncio
async def test_init_db_success(monkeypatch):
    """init_db should open a connection and run Base.metadata.create_all."""

    conn = _DummyConn()
    engine = _DummyEngine(conn)
    monkeypatch.setattr(init_module, "engine", engine)

    # Run
    result = await init_module.init_db()

    # Assertions
    assert result is None
    assert engine.begin_called is True
    assert conn.called_with is not None
    assert conn.called_with.__name__ == "create_all"


@pytest.mark.asyncio
async def test_init_db_error_propagation(monkeypatch):
    """If run_sync raises, the exception should propagate."""

    conn = _DummyConn(should_raise=True)
    engine = _DummyEngine(conn)
    monkeypatch.setattr(init_module, "engine", engine)

    with pytest.raises(ValueError):
        await init_module.init_db()
