# ruff: noqa: F403, F405
# Ensure project root on PYTHONPATH before importing app
import pathlib
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import Base and all models for Alembic autogenerate
from app.models import *

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata  # Set to Base.metadata for autogenerate

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url():
    """Return a *synchronous* SQLAlchemy URL for Alembic.

    The resolution order is:

    1. ``DATABASE_URL`` env var
    2. ``TEST_DB_URL`` env var (used by pytest/docker-compose.test.yml)
    3. Assemble from Postgres component env vars with sensible defaults.

    The function also **normalises** the value so it is *sync-driver* friendly –
    meaning any ``+asyncpg`` or ``+aiosqlite`` suffixes are stripped, because
    Alembic's synchronous engine creation paths cannot work with async
    dialects.
    """

    import os

    url: str | None = os.getenv("DATABASE_URL") or os.getenv("TEST_DB_URL")

    if not url:
        # Assemble from individual env vars (defaults mirror .env.example)
        user = os.getenv("POSTGRES_USER", "devuser")
        password = os.getenv("POSTGRES_PASSWORD", "devpass")
        server = os.getenv("POSTGRES_SERVER", "postgres-dev")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "smartwallet_dev")

        url = f"postgresql://{user}:{password}@{server}:{port}/{db}"

    # ------------------------------------------------------------------
    # Normalise: Alembic uses synchronous SQLAlchemy engines; strip async
    # driver markers so psycopg2 / default SQLite drivers are used.
    # ------------------------------------------------------------------

    if "+asyncpg" in url:
        url = url.replace("+asyncpg", "")
    if "+aiosqlite" in url:
        url = url.replace("+aiosqlite", "")

    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        {
            **config.get_section(config.config_ini_section, {}),
            "sqlalchemy.url": get_url(),
        },
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
