import uuid

import pytest
from fastapi import HTTPException

from app.repositories.wallet_repository import WalletRepository


@pytest.mark.asyncio
async def test_wallet_repository_crud(db_session):
    repo = WalletRepository(db_session)
    user_id = uuid.uuid4()
    addr = "0x1111111111111111111111111111111111111111"
    created = await repo.create(address=addr, name="Test", user_id=user_id)
    assert created.id is not None
    fetched = await repo.get_by_address(addr)
    assert fetched is not None and fetched.address == addr

    # list all
    all_wallets = await repo.list_by_user(user_id)
    assert len(all_wallets) >= 1

    # delete success
    assert await repo.delete(addr, user_id=user_id) is True
    assert await repo.get_by_address(addr) is None


@pytest.mark.asyncio
async def test_wallet_repository_delete_not_found(db_session):
    repo = WalletRepository(db_session)
    user_id = uuid.uuid4()
    with pytest.raises(HTTPException) as exc:
        await repo.delete("0x5555555555555555555555555555555555555555", user_id=user_id)
    assert exc.value.status_code == 404
