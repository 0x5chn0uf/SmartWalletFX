import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.schemas.wallet import WalletCreate
from app.usecase.wallet_usecase import WalletUsecase


@pytest.mark.asyncio
async def test_create_wallet_success(db_session):
    data = WalletCreate(
        address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd", name="UC"
    )
    usecase = WalletUsecase(db_session)
    wallet = await usecase.create_wallet(data)
    assert wallet.address == data.address
    assert wallet.name == "UC"


@pytest.mark.asyncio
async def test_create_wallet_duplicate(db_session):
    data = WalletCreate(address="0xabcdefabcdefabcdefabcdefabcdefabcdefabce")
    usecase = WalletUsecase(db_session)
    await usecase.create_wallet(data)
    with pytest.raises(HTTPException) as exc:
        await usecase.create_wallet(data)
    assert exc.value.status_code == 400
    assert "already exists" in exc.value.detail


@pytest.mark.asyncio
async def test_create_wallet_invalid_address(db_session):
    with pytest.raises(ValidationError):
        WalletCreate(address="notanaddress")


@pytest.mark.asyncio
async def test_list_wallets(db_session):
    usecase = WalletUsecase(db_session)
    await usecase.create_wallet(
        WalletCreate(address="0x1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a"),
    )
    await usecase.create_wallet(
        WalletCreate(address="0x2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b"),
    )
    wallets = await usecase.list_wallets()
    assert len(wallets) == 2


@pytest.mark.asyncio
async def test_delete_wallet_success(db_session):
    addr = "0x3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c"
    usecase = WalletUsecase(db_session)
    await usecase.create_wallet(WalletCreate(address=addr))
    await usecase.delete_wallet(addr)

    # Suppression d'un wallet inexistant
    with pytest.raises(HTTPException) as exc:
        await usecase.delete_wallet(addr)
    assert exc.value.status_code == 404
