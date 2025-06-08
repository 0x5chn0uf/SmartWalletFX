import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base

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
