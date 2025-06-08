import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models import Wallet
from app.schemas.wallet import WalletCreate
from app.usecase.wallet_usecase import WalletUsecase

TEST_DATABASE_URL = "sqlite:///./test_usecase.db"


@pytest.fixture(autouse=True)
def db_session():
    engine = create_engine(
        TEST_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(bind=engine)


def test_create_wallet_success(db_session):
    data = WalletCreate(
        address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd", name="UC"
    )
    wallet = WalletUsecase.create_wallet(db_session, data)
    assert wallet.address == data.address
    assert wallet.name == "UC"


def test_create_wallet_duplicate(db_session):
    data = WalletCreate(address="0xabcdefabcdefabcdefabcdefabcdefabcdefabce")
    WalletUsecase.create_wallet(db_session, data)
    with pytest.raises(HTTPException) as exc:
        WalletUsecase.create_wallet(db_session, data)
    assert exc.value.status_code == 400
    assert "already exists" in exc.value.detail


def test_create_wallet_invalid_address(db_session):
    data = WalletCreate(address="notanaddress")
    with pytest.raises(HTTPException) as exc:
        WalletUsecase.create_wallet(db_session, data)
    assert exc.value.status_code == 422
    assert "Invalid EVM address" in exc.value.detail


def test_list_wallets(db_session):
    WalletUsecase.create_wallet(
        db_session,
        WalletCreate(address="0x1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a"),
    )
    WalletUsecase.create_wallet(
        db_session,
        WalletCreate(address="0x2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b"),
    )
    wallets = WalletUsecase.list_wallets(db_session)
    assert len(wallets) == 2


def test_delete_wallet_success(db_session):
    addr = "0x3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c"
    WalletUsecase.create_wallet(db_session, WalletCreate(address=addr))
    WalletUsecase.delete_wallet(db_session, addr)
    # Suppression d'un wallet inexistant
    with pytest.raises(HTTPException) as exc:
        WalletUsecase.delete_wallet(db_session, addr)
    assert exc.value.status_code == 404
