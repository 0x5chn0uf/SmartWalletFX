"""Database session management with SQLAlchemy ORM."""

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from serena.core.models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLAlchemy database sessions and connections."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        if db_path is None:
            from serena import config
            db_path = config.memory_db_path()
            
        self.db_path = db_path
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Ensure database directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Create tables if they don't exist
        self._create_tables()

    def _create_engine(self) -> Engine:
        """Create SQLAlchemy engine with SQLite optimizations."""
        # Use sqlite:/// URL format for SQLAlchemy
        db_url = f"sqlite:///{self.db_path}"
        
        engine = create_engine(
            db_url,
            echo=False,  # Set to True for SQL debugging
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args={
                "check_same_thread": False,  # Allow multi-threading
            }
        )
        
        # Configure SQLite pragmas for performance
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.execute("PRAGMA mmap_size=268435456")  # 256MB
            cursor.close()
            
        return engine

    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables ready at %s", self.db_path)
        except Exception as exc:
            logger.error("Failed to create tables: %s", exc)
            raise

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup.
        
        Yields:
            Session: SQLAlchemy session
            
        Example:
            with db_manager.get_session() as session:
                archive = session.query(Archive).filter_by(task_id="123").first()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def get_transaction(self) -> Generator[Session, None, None]:
        """Get database session with explicit transaction control.
        
        Yields:
            Session: SQLAlchemy session (auto-commit disabled)
            
        Example:
            with db_manager.get_transaction() as session:
                # Make multiple changes
                session.add(archive1)
                session.add(archive2)
                # Commit happens automatically on success
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def health_check(self) -> bool:
        """Check database connectivity and basic operations.
        
        Returns:
            bool: True if database is healthy
        """
        try:
            with self.get_session() as session:
                # Simple query to test connectivity
                session.execute("SELECT 1").fetchone()
                return True
        except Exception as exc:
            logger.error("Database health check failed: %s", exc)
            return False

    def vacuum(self) -> None:
        """Run VACUUM operation to reclaim space."""
        try:
            # VACUUM requires a direct connection, not through session
            with self.engine.connect() as conn:
                conn.execute("VACUUM")
                conn.commit()
            logger.info("Database VACUUM completed")
        except Exception as exc:
            logger.error("Database VACUUM failed: %s", exc)
            raise

    def checkpoint(self) -> None:
        """Checkpoint the WAL file."""
        try:
            with self.engine.connect() as conn:
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                conn.commit()
            logger.info("WAL checkpoint completed")
        except Exception as exc:
            logger.error("WAL checkpoint failed: %s", exc)
            raise

    def close(self) -> None:
        """Close the database engine."""
        if hasattr(self, 'engine'):
            self.engine.dispose()


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager(db_path: Optional[str] = None) -> DatabaseManager:
    """Get global database manager instance.
    
    Args:
        db_path: Path to database file (only used on first call)
        
    Returns:
        DatabaseManager: Global database manager
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(db_path)
    return _db_manager


@contextmanager
def get_db_session(db_path: Optional[str] = None) -> Generator[Session, None, None]:
    """Convenience function to get a database session.
    
    Args:
        db_path: Path to database file
        
    Yields:
        Session: SQLAlchemy session
        
    Example:
        with get_db_session() as session:
            archives = session.query(Archive).limit(10).all()
    """
    db_manager = get_db_manager(db_path)
    with db_manager.get_session() as session:
        yield session