from __future__ import annotations

"""Centralised configuration using Pydantic Settings.

This replaces the previous bespoke ``serena.config`` layering with a single
``SerenaSettings`` object that automatically merges the following sources
(in order of precedence):

1. *Initialization kwargs* – values passed explicitly when instantiating
   ``SerenaSettings`` (used by CLI commands for --flag overrides).
2. *Environment variables* – variables prefixed with ``SERENA_``.
3. *serena/config.json* – user-editable file co-located with the package.
4. *Hard-coded defaults* defined on the dataclass fields.

An already-instantiated ``settings`` singleton is exposed for application-wide
use so existing code can simply do::

    from serena.settings import settings
    db_path = settings.memory_db

The legacy helper functions in ``serena.config`` have been re-implemented to
proxy to this object so external imports stay backward-compatible.
"""

from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


# ---------------------------------------------------------------------------
# Pydantic Settings implementation
# ---------------------------------------------------------------------------

class _Intervals(BaseModel):
    health_check: str = "1d"
    checkpoint: str = "7d"
    vacuum: str = "30d"


class _Enabled(BaseModel):
    health_check: bool = True
    checkpoint: bool = True
    vacuum: bool = True


class _Thresholds(BaseModel):
    large_db_size_mb: int = 1000
    large_entry_count: int = 100000
    warning_db_size_mb: int = 500
    critical_db_size_mb: int = 2000


class _Notifications(BaseModel):
    enable_console_output: bool = True
    enable_file_logging: bool = True
    log_file: str = str(Path(__file__).parent / "database" / "maintenance.log")


class _Performance(BaseModel):
    max_checkpoint_duration_seconds: int = 300
    max_vacuum_duration_seconds: int = 1800
    auto_optimize_intervals: bool = True


class _Backup(BaseModel):
    enable_pre_vacuum_backup: bool = False
    backup_directory: str = "database/backups"
    max_backup_files: int = 5


class MaintenanceConfig(BaseModel):
    """All tunables for automated database maintenance tasks."""

    intervals: _Intervals = _Intervals()
    enabled: _Enabled = _Enabled()
    thresholds: _Thresholds = _Thresholds()
    notifications: _Notifications = _Notifications()
    performance: _Performance = _Performance()
    backup: _Backup = _Backup()

    class Config:
        validate_assignment = True


class SerenaSettings(BaseSettings):
    """All runtime configuration for Serena in one place."""

    # Paths
    memory_db: str = Field(
        default=str(Path(__file__).parent / "database" / "memory_index.db"),
        env="SERENA_MEMORY_DB",
        description="Absolute path to the SQLite database used by Serena.",
    )

    # HTTP server
    server_url: str = Field(
        default="http://localhost:8765",
        env="SERENA_SERVER_URL",
        description="Base URL where a Serena HTTP server is running.",
    )

    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        env="SERENA_CORS_ORIGINS",
        description="Comma-separated list of Allowed CORS origins.",
    )
    cors_allow_credentials: bool = Field(
        default=True,
        env="SERENA_CORS_ALLOW_CREDENTIALS",
        description="Whether to allow credentials in CORS responses.",
    )
    cors_allow_methods: str = Field(
        default="GET,POST,PUT,DELETE,OPTIONS",
        env="SERENA_CORS_ALLOW_METHODS",
        description="Comma-separated list of HTTP methods for CORS.",
    )
    cors_allow_headers: str = Field(
        default="*",
        env="SERENA_CORS_ALLOW_HEADERS",
        description="Allowed request headers for CORS.",
    )

    # Embeddings / hardware
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        env="SERENA_EMBEDDING_MODEL",
        description="Name or path of the sentence-transformers model to use.",
    )
    device: str | None = Field(
        default=None,
        env="SERENA_DEVICE",
        description="Computation device override (cpu | cuda | mps).",
    )

    # Behaviour flags
    async_write: bool = Field(
        default=False,
        env="SERENA_ASYNC_WRITE",
        description="Write to DB via background queue instead of sync call.",
    )

    # Maintenance section (parsed from JSON defaults, override via env prefixes
    maintenance: MaintenanceConfig = Field(
        default_factory=MaintenanceConfig,
        description="Nested configuration for automated DB maintenance",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def cors_methods_list(self) -> list[str]:
        return [m.strip() for m in self.cors_allow_methods.split(",") if m.strip()]


# Singleton instance used throughout the package
settings = SerenaSettings() 