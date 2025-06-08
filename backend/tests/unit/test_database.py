import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models import Wallet

TEST_DATABASE_URL = "sqlite:///./test_model.db"


@pytest.fixture
def db_session():
    engine = create_engine(
        TEST_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    session = Session(engine)
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_create_wallet(db_session):
    wallet = Wallet(
        address="0x1234567890abcdef1234567890abcdef12345678",
        name="Test Wallet",
    )
    db_session.add(wallet)
    db_session.commit()
    assert wallet.id is not None
    assert wallet.address == "0x1234567890abcdef1234567890abcdef12345678"
    assert wallet.name == "Test Wallet"
