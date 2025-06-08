import asyncio

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.database import Base
from app.models import Wallet
from app.stores.wallet_store import WalletStore

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_store.db"


@pytest_asyncio.fixture(autouse=True)
async def db_session():
    engine = create_async_engine(
        TEST_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async_session = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    async with async_session() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


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
