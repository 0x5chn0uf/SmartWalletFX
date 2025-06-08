import pytest
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, engine

# Crée une session de base de données pour les tests
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def db_session():
    # Crée la base de données et les tables
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Supprime les tables après les tests
        Base.metadata.drop_all(bind=engine)


# Exemple de test


def test_example(db_session):
    # Remplacez ceci par un test réel
    assert True
