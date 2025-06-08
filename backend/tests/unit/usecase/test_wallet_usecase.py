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
    wallet = await WalletUsecase.create_wallet(db_session, data)
    assert wallet.address == data.address
    assert wallet.name == "UC"


@pytest.mark.asyncio
async def test_create_wallet_duplicate(db_session):
    data = WalletCreate(address="0xabcdefabcdefabcdefabcdefabcdefabcdefabce")
    await WalletUsecase.create_wallet(db_session, data)
    with pytest.raises(HTTPException) as exc:
        await WalletUsecase.create_wallet(db_session, data)
    assert exc.value.status_code == 400
    assert "already exists" in exc.value.detail


@pytest.mark.asyncio
async def test_create_wallet_invalid_address(db_session):
    with pytest.raises(ValidationError):
        WalletCreate(address="notanaddress")


@pytest.mark.asyncio
async def test_list_wallets(db_session):
    await WalletUsecase.create_wallet(
        db_session,
        WalletCreate(address="0x1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a"),
    )
    await WalletUsecase.create_wallet(
        db_session,
        WalletCreate(address="0x2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b"),
    )
    wallets = await WalletUsecase.list_wallets(db_session)
    assert len(wallets) == 2


@pytest.mark.asyncio
async def test_delete_wallet_success(db_session):
    addr = "0x3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c"
    await WalletUsecase.create_wallet(db_session, WalletCreate(address=addr))
    await WalletUsecase.delete_wallet(db_session, addr)
    # Suppression d'un wallet inexistant
    with pytest.raises(HTTPException) as exc:
        await WalletUsecase.delete_wallet(db_session, addr)
    assert exc.value.status_code == 404
