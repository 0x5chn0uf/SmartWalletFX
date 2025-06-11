import pytest
from fastapi import HTTPException

from app.stores.wallet_store import WalletStore


@pytest.mark.asyncio
async def test_create_and_get_wallet(db_session):
    addr = "0x1111111111111111111111111111111111111111"
    created = await WalletStore.create(db_session, address=addr, name="Test")
    assert created.id is not None
    fetched = await WalletStore.get_by_address(db_session, addr)
    assert fetched is not None
    assert fetched.address == addr
    assert fetched.name == "Test"


@pytest.mark.asyncio
async def test_list_all_wallets(db_session):
    await WalletStore.create(
        db_session, address="0x2222222222222222222222222222222222222222"
    )
    await WalletStore.create(
        db_session, address="0x3333333333333333333333333333333333333333"
    )
    wallets = await WalletStore.list_all(db_session)
    assert len(wallets) == 2


@pytest.mark.asyncio
async def test_delete_wallet(db_session):
    addr = "0x4444444444444444444444444444444444444444"
    await WalletStore.create(db_session, address=addr)
    assert await WalletStore.delete(db_session, addr) is True
    assert await WalletStore.get_by_address(db_session, addr) is None
    # Suppression d'un wallet inexistant
    with pytest.raises(HTTPException) as exc:
        await WalletStore.delete(
            db_session, "0x5555555555555555555555555555555555555555"
        )
    assert exc.value.status_code == 404
