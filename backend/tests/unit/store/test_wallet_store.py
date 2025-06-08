import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models import Wallet
from app.stores.wallet_store import WalletStore

TEST_DATABASE_URL = "sqlite:///./test_store.db"


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


def test_create_and_get_wallet(db_session):
    addr = "0x1111111111111111111111111111111111111111"
    created = WalletStore.create(db_session, address=addr, name="Test")
    assert created.id is not None
    fetched = WalletStore.get_by_address(db_session, addr)
    assert fetched is not None
    assert fetched.address == addr
    assert fetched.name == "Test"


def test_list_all_wallets(db_session):
    WalletStore.create(
        db_session, address="0x2222222222222222222222222222222222222222"
    )
    WalletStore.create(
        db_session, address="0x3333333333333333333333333333333333333333"
    )
    wallets = WalletStore.list_all(db_session)
    assert len(wallets) == 2


def test_delete_wallet(db_session):
    addr = "0x4444444444444444444444444444444444444444"
    WalletStore.create(db_session, address=addr)
    assert WalletStore.delete(db_session, addr) is True
    assert WalletStore.get_by_address(db_session, addr) is None
    # Suppression d'un wallet inexistant
    assert (
        WalletStore.delete(
            db_session, "0x5555555555555555555555555555555555555555"
        )
        is False
    )
