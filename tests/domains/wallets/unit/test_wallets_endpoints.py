import uuid
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import Request

from app.api.endpoints.wallets import Wallets
from app.domain.schemas.wallet import WalletCreate, WalletResponse


@pytest.fixture
def _setup_wallets_endpoint():
    """Return Wallets endpoint class wired with mocked use-cases."""
    fake_wallet_uc = AsyncMock()
    # other UCs are not used in these tests; pass AsyncMocks to satisfy signature
    Wallets(
        fake_wallet_uc,
        AsyncMock(),
        AsyncMock(),
        AsyncMock(),
        AsyncMock(),
        AsyncMock(),
    )
    return Wallets, fake_wallet_uc


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_wallets_success(_setup_wallets_endpoint):
    endpoint_cls, wallet_uc = _setup_wallets_endpoint

    uid = uuid.uuid4()
    example_wallet = WalletResponse(
        id=uuid.uuid4(),
        user_id=uid,
        address="0x" + "b" * 40,
        name="Main",
        is_active=True,
        balance_usd=123.45,
    )
    wallet_uc.list_wallets.return_value = [example_wallet]

    req = Mock(spec=Request)
    req.client = Mock(host="127.0.0.1")

    with patch("app.api.endpoints.wallets.get_user_id_from_request", return_value=uid):
        result = await endpoint_cls.list_wallets(req)
        assert result == [example_wallet]
        wallet_uc.list_wallets.assert_awaited_once_with(uid)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_wallet_success(_setup_wallets_endpoint):
    endpoint_cls, wallet_uc = _setup_wallets_endpoint
    uid = uuid.uuid4()

    create_payload = WalletCreate(address="0x" + "a" * 40, name="Main")
    created = WalletResponse(
        id=uuid.uuid4(),
        user_id=uid,
        address="0x" + "a" * 40,
        name="Main",
        is_active=True,
        balance_usd=0.0,
    )
    wallet_uc.create_wallet.return_value = created

    req = Mock(spec=Request)
    req.client = Mock(host="127.0.0.1")

    with patch("app.api.endpoints.wallets.get_user_id_from_request", return_value=uid):
        result = await endpoint_cls.create_wallet(req, create_payload)
        assert result == created
        wallet_uc.create_wallet.assert_awaited_once_with(uid, create_payload)
