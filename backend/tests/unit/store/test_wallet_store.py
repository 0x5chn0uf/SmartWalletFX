import pytest
from fastapi import HTTPException

from app.repositories.wallet_repository import WalletRepository


@pytest.mark.asyncio
async def test_create_and_get_wallet(db_session):
    store = WalletRepository(db_session)
    addr = "0x1111111111111111111111111111111111111111"
    created = await store.create(address=addr, name="Test")
    assert created.id is not None
    fetched = await store.get_by_address(addr)
    assert fetched is not None
    assert fetched.address == addr
    assert fetched.name == "Test"


@pytest.mark.asyncio
async def test_list_all_wallets(db_session):
    store = WalletRepository(db_session)
    await store.create(address="0x2222222222222222222222222222222222222222")
    await store.create(address="0x3333333333333333333333333333333333333333")
    wallets = await store.list_all()
    assert len(wallets) == 2


@pytest.mark.asyncio
async def test_delete_wallet(db_session):
    store = WalletRepository(db_session)
    addr = "0x4444444444444444444444444444444444444444"
    await store.create(address=addr)
    assert await store.delete(addr) is True
    assert await store.get_by_address(addr) is None
    # Suppression d'un wallet inexistant
    with pytest.raises(HTTPException) as exc:
        await store.delete("0x5555555555555555555555555555555555555555")
    assert exc.value.status_code == 404
