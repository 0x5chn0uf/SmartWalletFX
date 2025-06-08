from app.core.database import Base, engine


def init_db() -> None:
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(bind=engine)
