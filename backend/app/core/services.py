from __future__ import annotations

import threading
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import Settings
from celery import Celery
from celery.schedules import crontab

from app.core.settings_service import SettingsService
from app.utils.logging import LoggingService


class DatabaseService:
    """Manage asynchronous and synchronous database engines."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._lock = threading.Lock()
        self._engine: Optional[any] = None
        self._SessionLocal: Optional[async_sessionmaker[AsyncSession]] = None
        self._sync_engine: Optional[any] = None
        self._SyncSessionLocal: Optional[sessionmaker] = None
        self.Base = declarative_base()
        self._init_engines()

    # ------------------------------------------------------------------
    # Engine/session creation helpers
    # ------------------------------------------------------------------
    def _init_engines(self) -> None:
        """Initialise SQLAlchemy engines from settings."""
        db_url = self._settings.DATABASE_URL
        if db_url.startswith("sqlite:///") and "+aiosqlite" not in db_url:
            db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///")
        elif db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

        connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
        pool_kwargs = {}
        if "postgresql" in db_url:
            pool_kwargs = {
                "pool_size": self._settings.DB_POOL_SIZE,
                "max_overflow": self._settings.DB_MAX_OVERFLOW,
            }

        self._engine = create_async_engine(
            db_url, connect_args=connect_args, **pool_kwargs
        )
        self._SessionLocal = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        sync_db_url = self._settings.DATABASE_URL
        if "+aiosqlite" in sync_db_url:
            sync_db_url = sync_db_url.replace("+aiosqlite", "")
        elif "+asyncpg" in sync_db_url:
            sync_db_url = sync_db_url.replace("+asyncpg", "")

        self._sync_engine = create_engine(
            sync_db_url,
            connect_args={"check_same_thread": False}
            if "sqlite" in sync_db_url
            else {},
        )
        self._SyncSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self._sync_engine
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @property
    def engine(self):
        return self._engine

    @property
    def SessionLocal(self):
        return self._SessionLocal

    @property
    def sync_engine(self):
        return self._sync_engine

    @property
    def SyncSessionLocal(self):
        return self._SyncSessionLocal

    async def get_db(self) -> Generator[AsyncSession, None, None]:
        async with self._SessionLocal() as session:  # type: ignore
            yield session


class CeleryService:
    """Wrap Celery app creation and configuration."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._app = Celery(
            "SmartWalletFX",
            broker="redis://localhost:6379/0",
            backend="redis://localhost:6379/0",
        )
        self._app.conf.timezone = "UTC"
        self._app.conf.beat_schedule = {
            "collect-snapshots-every-hours": {
                "task": "app.tasks.snapshots.collect_portfolio_snapshots",
                "schedule": crontab(hour="*", minute="0"),
            },
            "db-backup-daily": {
                "task": "app.tasks.backups.create_backup_task",
                "schedule": crontab(hour=2, minute=0),
            },
            "jwt-rotation-beat": {
                "task": "app.tasks.jwt_rotation.promote_and_retire_keys_task",
                "schedule": crontab(minute="*/5"),
            },
        }

        self._update_schedule_from_settings()

    def _update_schedule_from_settings(self) -> None:
        self._app.conf.beat_schedule["jwt-rotation-beat"]["schedule"] = crontab(
            *self._settings.JWT_ROTATION_SCHEDULE_CRON.split()
        )

    @property
    def app(self) -> Celery:
        return self._app


class ServiceContainer:
    """Simple service container for dependency management."""

    def __init__(self, settings_service: SettingsService | None = None, *, load_celery: bool = True) -> None:
        self.settings_service = settings_service or SettingsService()
        self.database_service = DatabaseService(self.settings_service.settings)
        self.celery_service = (
            CeleryService(self.settings_service.settings) if load_celery else None
        )
        self.logging_service = LoggingService()

    # Convenience accessors -------------------------------------------------
    @property
    def settings(self) -> Settings:
        return self.settings_service.settings

    @property
    def db(self) -> DatabaseService:
        return self.database_service

    @property
    def celery(self) -> CeleryService:
        assert self.celery_service is not None, "CeleryService not enabled"
        return self.celery_service

    @property
    def logging(self) -> LoggingService:
        return self.logging_service
