import inspect

import pytest
from fastapi import HTTPException

import app.api.dependencies as deps_mod
from app.api.dependencies import (
    _build_aggregator_async,
    auth_deps,
    blockchain_deps,
)


@pytest.fixture(autouse=True)
def _clear_w3_cache():
    """Ensure the Web3 provider cache is cleared before & after each test."""
    blockchain_deps.get_w3.cache_clear()
    yield
    blockchain_deps.get_w3.cache_clear()


# ---------------------------------------------------------------------------
# get_w3 (cached) helper
# ---------------------------------------------------------------------------


def test_get_w3_returns_cached_instance(monkeypatch):
    """Calling get_w3 twice should return the same (cached) instance."""

    # Dummy Web3 replacement that records the provided URI
    class DummyWeb3:
        class HTTPProvider:  # noqa: D101 – minimal stub
            def __init__(self, uri):
                self.uri = uri

        def __init__(self, provider):
            # *provider* will be an instance of DummyWeb3.HTTPProvider
            self.provider = provider

    monkeypatch.setattr(deps_mod, "Web3", DummyWeb3)

    first = blockchain_deps.get_w3()
    second = blockchain_deps.get_w3()

    assert first is second  # cached instance
    assert isinstance(first, DummyWeb3)
    # Ensure the provider URI passed to HTTPProvider matches default setting
    from app.core.config import settings

    assert first.provider.uri == getattr(
        settings, "WEB3_PROVIDER_URI", "https://ethereum-rpc.publicnode.com"
    )


# ---------------------------------------------------------------------------
# _build_aggregator_async helper
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_aggregator_async_invokes_usecase(monkeypatch):
    """Ensure the aggregator returned by _build_aggregator_async delegates to the underlying use-case."""

    captured = {}

    class DummyUsecase:  # noqa: D101 – test double
        async def aggregate_portfolio_metrics(self, address):
            captured["address"] = address
            return "METRICS"

    monkeypatch.setattr(deps_mod, "PortfolioAggregationUsecase", DummyUsecase)

    aggregator = _build_aggregator_async()
    assert inspect.iscoroutinefunction(aggregator)

    result = await aggregator("0x123")
    assert result == "METRICS"
    assert captured["address"] == "0x123"


# ---------------------------------------------------------------------------
# get_current_user – positive and negative paths
# ---------------------------------------------------------------------------


class DummyUser:  # noqa: D101 – simple stand-in object
    pass


class DummySession:  # noqa: D101 – async session stub
    def __init__(self, user: DummyUser | None):
        self._user = user

    async def get(self, model, pk):  # noqa: D401 – mimic SQLAlchemy AsyncSession.get
        return self._user


@pytest.mark.asyncio
async def test_get_current_user_success(monkeypatch):
    """A valid token with an existing user returns the user instance."""

    user = DummyUser()
    monkeypatch.setattr(
        deps_mod.JWTUtils,
        "decode_token",
        lambda token: {"sub": "42", "roles": ["user"]},
    )
    session = DummySession(user)

    result = await auth_deps.get_current_user(token="token", db=session)
    assert result is user


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "decoded, expected_detail",
    [
        (Exception("boom"), "Invalid authentication credentials"),
        ({}, "Token missing subject claim"),
        ({"sub": "abc"}, "Invalid subject in token"),
        ({"sub": "123"}, "User not found"),
    ],
)
async def test_get_current_user_error_paths(monkeypatch, decoded, expected_detail):
    """Verify each error branch raises HTTPException with the correct detail message."""

    # Patch decode_token to either raise or return custom value
    if isinstance(decoded, Exception):

        def _raise(_):
            raise decoded

        monkeypatch.setattr(deps_mod.JWTUtils, "decode_token", _raise)
    else:
        monkeypatch.setattr(deps_mod.JWTUtils, "decode_token", lambda _: decoded)

    # Prepare session that returns *None* to trigger "user not found" branch
    session = DummySession(user=None)

    with pytest.raises(HTTPException) as exc:
        await auth_deps.get_current_user(token="whatever", db=session)

    assert exc.value.status_code == 401
    assert expected_detail in exc.value.detail
