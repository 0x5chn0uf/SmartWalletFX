from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Configuration
from app.core.database import Base, CoreDatabase
from app.utils.logging import Audit


class TestCoreDatabase:
    """Test CoreDatabase class."""

    def test_init_with_sqlite_async_url(self):
        """Test initialization with SQLite database URL conversion."""
        config = Mock(spec=Configuration)
        config.DATABASE_URL = "sqlite:///test.db"
        config.DB_POOL_SIZE = 10
        config.DB_MAX_OVERFLOW = 20

        audit = Mock(spec=Audit)

        with patch("app.core.database.create_async_engine") as mock_create_async, patch(
            "app.core.database.create_engine"
        ) as mock_create_sync, patch("app.core.database.async_sessionmaker"), patch(
            "app.core.database.sessionmaker"
        ):
            CoreDatabase(config, audit)

            # Check that SQLite URL was converted to aiosqlite
            mock_create_async.assert_called_once()
            args, kwargs = mock_create_async.call_args
            assert args[0] == "sqlite+aiosqlite:///test.db"
            assert kwargs["connect_args"] == {"check_same_thread": False}

            # Check sync engine setup
            mock_create_sync.assert_called_once()
            sync_args, sync_kwargs = mock_create_sync.call_args
            assert sync_args[0] == "sqlite:///test.db"
            assert sync_kwargs["connect_args"] == {"check_same_thread": False}

    def test_init_with_postgresql_url(self):
        """Test initialization with PostgreSQL database URL conversion."""
        config = Mock(spec=Configuration)
        config.DATABASE_URL = "postgresql://user:pass@host:5432/db"
        config.DB_POOL_SIZE = 10
        config.DB_MAX_OVERFLOW = 20

        audit = Mock(spec=Audit)

        with patch("app.core.database.create_async_engine") as mock_create_async, patch(
            "app.core.database.create_engine"
        ) as mock_create_sync, patch("app.core.database.async_sessionmaker"), patch(
            "app.core.database.sessionmaker"
        ):
            CoreDatabase(config, audit)

            # Check that PostgreSQL URL was converted to asyncpg
            mock_create_async.assert_called_once()
            args, kwargs = mock_create_async.call_args
            assert args[0] == "postgresql+asyncpg://user:pass@host:5432/db"
            assert kwargs["connect_args"] == {}
            assert kwargs["pool_size"] == 10
            assert kwargs["max_overflow"] == 20

            # Check sync engine setup
            mock_create_sync.assert_called_once()
            sync_args, sync_kwargs = mock_create_sync.call_args
            assert sync_args[0] == "postgresql://user:pass@host:5432/db"
            assert sync_kwargs["connect_args"] == {}

    def test_init_with_already_async_urls(self):
        """Test initialization with already converted async URLs."""
        config = Mock(spec=Configuration)
        config.DATABASE_URL = "sqlite+aiosqlite:///test.db"
        config.DB_POOL_SIZE = 10
        config.DB_MAX_OVERFLOW = 20

        audit = Mock(spec=Audit)

        with patch("app.core.database.create_async_engine") as mock_create_async, patch(
            "app.core.database.create_engine"
        ) as mock_create_sync, patch("app.core.database.async_sessionmaker"), patch(
            "app.core.database.sessionmaker"
        ):
            CoreDatabase(config, audit)

            # Check that URL was not double-converted
            mock_create_async.assert_called_once()
            args, kwargs = mock_create_async.call_args
            assert args[0] == "sqlite+aiosqlite:///test.db"

            # Check sync engine setup removes async driver
            mock_create_sync.assert_called_once()
            sync_args, sync_kwargs = mock_create_sync.call_args
            assert sync_args[0] == "sqlite:///test.db"

    def test_init_with_postgresql_asyncpg_url(self):
        """Test initialization with PostgreSQL asyncpg URL conversion."""
        config = Mock(spec=Configuration)
        config.DATABASE_URL = "postgresql+asyncpg://user:pass@host:5432/db"
        config.DB_POOL_SIZE = 10
        config.DB_MAX_OVERFLOW = 20

        audit = Mock(spec=Audit)

        with patch("app.core.database.create_async_engine") as mock_create_async, patch(
            "app.core.database.create_engine"
        ) as mock_create_sync, patch("app.core.database.async_sessionmaker"), patch(
            "app.core.database.sessionmaker"
        ):
            CoreDatabase(config, audit)

            # Check that URL was not double-converted
            mock_create_async.assert_called_once()
            args, kwargs = mock_create_async.call_args
            assert args[0] == "postgresql+asyncpg://user:pass@host:5432/db"

            # Check sync engine setup removes async driver
            mock_create_sync.assert_called_once()
            sync_args, sync_kwargs = mock_create_sync.call_args
            assert sync_args[0] == "postgresql://user:pass@host:5432/db"

    @pytest.mark.asyncio
    async def test_init_db_success(self):
        """Test successful database initialization."""
        config = Mock(spec=Configuration)
        config.DATABASE_URL = "sqlite:///test.db"
        config.DB_POOL_SIZE = 10
        config.DB_MAX_OVERFLOW = 20

        audit = Mock(spec=Audit)

        with patch("app.core.database.create_async_engine") as mock_create_async, patch(
            "app.core.database.create_engine"
        ), patch("app.core.database.async_sessionmaker"), patch(
            "app.core.database.sessionmaker"
        ):
            # Mock the async engine and connection
            mock_engine = Mock()
            mock_conn = Mock()
            mock_conn.run_sync = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_engine.begin.return_value = mock_context

            mock_create_async.return_value = mock_engine

            db = CoreDatabase(config, audit)

            # Test init_db
            await db.init_db()

            audit.info.assert_any_call("database_initialization_started")
            audit.info.assert_any_call("database_initialization_completed")
            mock_conn.run_sync.assert_called_once_with(Base.metadata.create_all)

    @pytest.mark.asyncio
    async def test_init_db_failure(self):
        """Test database initialization failure."""
        config = Mock(spec=Configuration)
        config.DATABASE_URL = "sqlite:///test.db"
        config.DB_POOL_SIZE = 10
        config.DB_MAX_OVERFLOW = 20

        audit = Mock(spec=Audit)

        with patch("app.core.database.create_async_engine") as mock_create_async, patch(
            "app.core.database.create_engine"
        ), patch("app.core.database.async_sessionmaker"), patch(
            "app.core.database.sessionmaker"
        ):
            # Mock the async engine and connection to raise an exception
            mock_engine = Mock()
            mock_conn = Mock()
            mock_conn.run_sync = AsyncMock(side_effect=Exception("DB Error"))
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_engine.begin.return_value = mock_context

            mock_create_async.return_value = mock_engine

            db = CoreDatabase(config, audit)

            # Test init_db failure
            with pytest.raises(Exception, match="DB Error"):
                await db.init_db()

            audit.info.assert_called_once_with("database_initialization_started")
            audit.error.assert_called_once_with(
                "database_initialization_failed", error="DB Error"
            )

    @pytest.mark.asyncio
    async def test_check_database_connection_success(self):
        """Test successful database connection check."""
        config = Mock(spec=Configuration)
        config.DATABASE_URL = "sqlite:///test.db"
        config.DB_POOL_SIZE = 10
        config.DB_MAX_OVERFLOW = 20

        audit = Mock(spec=Audit)

        with patch("app.core.database.create_async_engine") as mock_create_async, patch(
            "app.core.database.create_engine"
        ), patch("app.core.database.async_sessionmaker"), patch(
            "app.core.database.sessionmaker"
        ):
            # Mock the async engine and connection
            mock_engine = Mock()
            mock_conn = Mock()
            mock_conn.execute = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_engine.begin.return_value = mock_context

            mock_create_async.return_value = mock_engine

            db = CoreDatabase(config, audit)

            # Test connection check
            result = await db.check_database_connection()

            assert result is True
            mock_conn.execute.assert_called_once_with("SELECT 1")

    @pytest.mark.asyncio
    async def test_check_database_connection_failure(self):
        """Test database connection check failure."""
        config = Mock(spec=Configuration)
        config.DATABASE_URL = "sqlite:///test.db"
        config.DB_POOL_SIZE = 10
        config.DB_MAX_OVERFLOW = 20

        audit = Mock(spec=Audit)

        with patch("app.core.database.create_async_engine") as mock_create_async, patch(
            "app.core.database.create_engine"
        ), patch("app.core.database.async_sessionmaker"), patch(
            "app.core.database.sessionmaker"
        ):
            # Mock the async engine and connection to raise an exception
            mock_engine = Mock()
            mock_conn = Mock()
            mock_conn.execute = AsyncMock(side_effect=Exception("Connection Error"))
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_engine.begin.return_value = mock_context

            mock_create_async.return_value = mock_engine

            db = CoreDatabase(config, audit)

            # Test connection check failure
            result = await db.check_database_connection()

            assert result is False
            audit.error.assert_called_once_with(
                "database_connection_check_failed", error="Connection Error"
            )

    @pytest.mark.asyncio
    async def test_get_session(self):
        """Test get_session async context manager."""
        config = Mock(spec=Configuration)
        config.DATABASE_URL = "sqlite:///test.db"
        config.DB_POOL_SIZE = 10
        config.DB_MAX_OVERFLOW = 20

        audit = Mock(spec=Audit)

        with patch("app.core.database.create_async_engine"), patch(
            "app.core.database.create_engine"
        ), patch("app.core.database.async_sessionmaker") as mock_async_session, patch(
            "app.core.database.sessionmaker"
        ):
            # Mock the session factory
            mock_session_instance = Mock(spec=AsyncSession)
            mock_session_context = AsyncMock()
            mock_session_context.__aenter__ = AsyncMock(
                return_value=mock_session_instance
            )
            mock_session_context.__aexit__ = AsyncMock(return_value=None)
            mock_session_factory = Mock(return_value=mock_session_context)
            mock_async_session.return_value = mock_session_factory

            db = CoreDatabase(config, audit)

            # Test get_session
            async with db.get_session() as session:
                assert session is mock_session_instance

    def test_get_sync_session(self):
        """Test get_sync_session method."""
        config = Mock(spec=Configuration)
        config.DATABASE_URL = "sqlite:///test.db"
        config.DB_POOL_SIZE = 10
        config.DB_MAX_OVERFLOW = 20

        audit = Mock(spec=Audit)

        with patch("app.core.database.create_async_engine"), patch(
            "app.core.database.create_engine"
        ), patch("app.core.database.async_sessionmaker"), patch(
            "app.core.database.sessionmaker"
        ) as mock_session:
            # Mock the sync session factory
            mock_session_instance = Mock()
            mock_session_factory = Mock(return_value=mock_session_instance)
            mock_session.return_value = mock_session_factory

            db = CoreDatabase(config, audit)

            # Test get_sync_session
            session = db.get_sync_session()
            assert session is mock_session_instance
