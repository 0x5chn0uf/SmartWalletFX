import inspect

import pytest

from app import di


@pytest.mark.asyncio
async def test_build_aggregator_calls_usecase(monkeypatch):
    """_build_aggregator should return an async callable that delegates to PortfolioAggregationUsecase."""

    captured = {}

    class FakeUsecase:  # noqa: D101 – simple test double
        async def aggregate_portfolio_metrics(self, address: str):  # noqa: D401
            """Pretend to aggregate metrics and capture the address."""
            captured["address"] = address
            return "dummy-metrics"

    # Replace the real use-case class with our fake implementation
    monkeypatch.setattr(di, "PortfolioAggregationUsecase", FakeUsecase)

    # Build the aggregator and verify its characteristics
    aggregator = di._build_aggregator()
    assert inspect.iscoroutinefunction(aggregator)

    # Call the aggregator and ensure it forwarded the address correctly
    result = await aggregator("0xabc")
    assert result == "dummy-metrics"
    assert captured["address"] == "0xabc"


@pytest.mark.asyncio
async def test_aggregator_closes_over_instance(monkeypatch):
    """The aggregator should keep a reference to the *original* usecase instance even if patched later."""

    class FirstUsecase:  # noqa: D101 – test double
        async def aggregate_portfolio_metrics(self, address: str):
            return "first"

    # Patch with *first* implementation when building the aggregator
    monkeypatch.setattr(di, "PortfolioAggregationUsecase", FirstUsecase)
    aggregator = di._build_aggregator()

    # Patch again with a *different* implementation AFTER the aggregator has been built
    class SecondUsecase:  # noqa: D101 – another test double
        async def aggregate_portfolio_metrics(self, address: str):
            return "second"

    monkeypatch.setattr(di, "PortfolioAggregationUsecase", SecondUsecase)

    # Even though the global reference has changed, the aggregator should still call the *FirstUsecase* instance.
    assert await aggregator("0xdef") == "first"


@pytest.mark.asyncio
async def test_get_session_sync_returns_custom(monkeypatch):
    """Ensure get_session_sync returns the object created by SyncSessionLocal factory."""

    class DummySession:  # noqa: D101 – simple stand-in for SQLAlchemy Session
        pass

    factory_called = {}

    def dummy_factory():  # noqa: D401 – test helper
        factory_called["called"] = True
        return DummySession()

    # Patch the session factory used inside DI module
    monkeypatch.setattr(di, "SyncSessionLocal", dummy_factory)

    # Because get_session_sync is a thin wrapper, it should return the object from our dummy factory.
    session = di.get_session_sync()
    assert isinstance(session, DummySession)
    assert factory_called.get("called") is True


def test_get_snapshot_service_sync(monkeypatch):
    """Validate that get_snapshot_service_sync wires SnapshotAggregationService with correct args."""

    class DummyService:  # noqa: D101 – stand-in for actual service
        def __init__(self, session, agg):
            self.session = session
            self.agg = agg

    # Prepare patches
    dummy_session = object()
    monkeypatch.setattr(di, "get_session_sync", lambda *_, **__: dummy_session)
    monkeypatch.setattr(di, "_build_aggregator", lambda: "agg")
    monkeypatch.setattr(di, "SnapshotAggregationService", DummyService)

    service = di.get_snapshot_service_sync()

    # Ensure our DummyService was instantiated with patched dependencies
    assert isinstance(service, DummyService)
    assert service.session is dummy_session
    assert service.agg == "agg"
