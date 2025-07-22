# Database Patterns Guide

> **Audience**: Claude Code and contributors working with database operations
> **Purpose**: Essential patterns for database architecture, repositories, and migrations

## 1. Repository Constructor Patterns

### Standard Repository Structure

All repositories follow consistent dependency injection and audit logging patterns:

```python
from app.core.database import CoreDatabase
from app.utils.logging import Audit
from typing import Optional
import uuid

class ExampleRepository:
    """Repository for Example entity CRUD operations."""

    def __init__(self, database: CoreDatabase, audit: Audit):
        self.__database = database
        self.__audit = audit

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[ExampleEntity]:
        """Get entity by ID with audit logging."""
        self.__audit.info("repository_get_by_id_started", entity_id=str(entity_id))

        try:
            async with self.__database.get_session() as session:
                entity = await session.get(ExampleEntity, entity_id)

                self.__audit.info(
                    "repository_get_by_id_success",
                    entity_id=str(entity_id),
                    found=entity is not None,
                )
                return entity

        except Exception as e:
            self.__audit.error(
                "repository_get_by_id_failed",
                entity_id=str(entity_id),
                error=str(e),
            )
            raise
```

### Key Repository Principles

1. **Private attributes**: Use `self.__database` and `self.__audit` (double underscore)
2. **Audit everything**: Log start, success, and failure for all operations
3. **Context managers**: Always use `async with self.__database.get_session()`
4. **Exception handling**: Catch, log, and re-raise all exceptions
5. **Type hints**: Use `Optional[Entity]` for single results, `list[Entity]` for multiple

### Session Management Pattern

```python
async def save(self, entity: ExampleEntity) -> ExampleEntity:
    """Save entity with proper session management."""
    self.__audit.info("repository_save_started", entity_id=str(entity.id) if entity.id else None)

    try:
        async with self.__database.get_session() as session:
            session.add(entity)

            try:
                await session.commit()
            except IntegrityError as e:
                self.__audit.error("repository_save_integrity_error", error=str(e))
                await session.rollback()
                raise

            await session.refresh(entity)

            self.__audit.info("repository_save_success", entity_id=str(entity.id))
            return entity

    except Exception as e:
        self.__audit.error("repository_save_failed", error=str(e))
        raise
```

## 2. Migration Best Practices with Alembic

### Migration File Structure

```python
"""descriptive_migration_name

Revision ID: 0001_init
Revises:
Create Date: 2025-06-11 10:10:11.377969
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic
revision: str = "0001_init"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    # Forward migration code

def downgrade() -> None:
    """Downgrade schema."""
    # Reverse migration code
```

### Table Creation Patterns

```python
def upgrade() -> None:
    """Create users table with proper indexing."""
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True, default=True),
        sa.Column("is_verified", sa.Boolean(), nullable=True, default=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for performance
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

def downgrade() -> None:
    """Drop users table and indexes."""
    op.execute("DROP INDEX IF EXISTS ix_users_username")
    op.execute("DROP INDEX IF EXISTS ix_users_email")
    op.execute("DROP INDEX IF EXISTS ix_users_id")
    op.drop_table("users")
```

### Foreign Key Patterns

```python
def upgrade() -> None:
    """Create wallets table with foreign key to users."""
    op.create_table(
        "wallets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("address", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("balance", sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column("balance_usd", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Performance indexes
    op.create_index(op.f("ix_wallets_user_id"), "wallets", ["user_id"], unique=False)
    op.create_index(op.f("ix_wallets_address"), "wallets", ["address"], unique=True)
```

### Column Type Guidelines

```python
# UUIDs for primary keys
sa.Column("id", sa.UUID(), nullable=False)

# String fields with appropriate lengths
sa.Column("username", sa.String(length=50), nullable=False)
sa.Column("email", sa.String(length=255), nullable=False)

# Precise decimals for financial data
sa.Column("balance", sa.Numeric(precision=36, scale=18), nullable=False)
sa.Column("price_usd", sa.Numeric(precision=18, scale=8), nullable=True)

# Timestamps
sa.Column("created_at", sa.DateTime(), nullable=True)
sa.Column("updated_at", sa.DateTime(), nullable=True)

# Boolean flags with defaults
sa.Column("is_active", sa.Boolean(), nullable=True, default=True)

# JSON for flexible metadata
sa.Column("extra_metadata", sa.JSON(), nullable=True)
```

## 3. Async SQLAlchemy 2.0 Conventions

### Database Connection Setup

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from contextlib import asynccontextmanager

class CoreDatabase:
    """Database service managing async connections."""

    def __init__(self, config: Configuration, audit: Audit):
        self.config = config
        self.audit = audit
        self._setup_async_engine()
        self._setup_session_factories()

    def _setup_async_engine(self):
        """Set up async database engine with proper drivers."""
        db_url = self.config.DATABASE_URL

        # Handle async drivers
        if db_url.startswith("sqlite:///") and "+aiosqlite" not in db_url:
            db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///")
        elif db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

        # Connection pooling for PostgreSQL
        pool_kwargs = {}
        if "postgresql" in str(db_url):
            pool_kwargs = {
                "pool_size": self.config.DB_POOL_SIZE,
                "max_overflow": self.config.DB_MAX_OVERFLOW,
            }

        self.async_engine = create_async_engine(db_url, **pool_kwargs)

    def _setup_session_factories(self):
        """Configure session factory."""
        self.async_session_factory = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Important for async
        )

    @asynccontextmanager
    async def get_session(self):
        """Get async database session context manager."""
        async with self.async_session_factory() as session:
            yield session
```

### Query Patterns

#### Simple Queries

```python
from sqlalchemy import select

async def get_by_username(self, username: str) -> Optional[User]:
    """Get user by username using modern select syntax."""
    async with self.__database.get_session() as session:
        stmt = select(User).filter_by(username=username)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

async def get_all_active(self) -> list[User]:
    """Get all active users."""
    async with self.__database.get_session() as session:
        stmt = select(User).where(User.is_active == True)
        result = await session.execute(stmt)
        return result.scalars().all()
```

#### Complex Queries with Joins

```python
async def get_user_wallets(self, user_id: uuid.UUID) -> list[Wallet]:
    """Get all wallets for a user with token balances."""
    async with self.__database.get_session() as session:
        stmt = (
            select(Wallet)
            .where(Wallet.user_id == user_id)
            .where(Wallet.is_active == True)
            .order_by(Wallet.created_at.desc())
        )
        result = await session.execute(stmt)
        return result.scalars().all()
```

#### Exists Queries

```python
async def exists(self, *, username: str | None = None, email: str | None = None) -> bool:
    """Check if user exists with given criteria."""
    async with self.__database.get_session() as session:
        stmt = select(User.id)
        if username is not None:
            stmt = stmt.filter_by(username=username)
        if email is not None:
            stmt = stmt.filter_by(email=email)

        result = await session.execute(stmt.limit(1))
        return result.scalar_one_or_none() is not None
```

### Model Definition Patterns

```python
from sqlalchemy import Column, String, DateTime, Boolean, UUID, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime

class User(Base):
    """User model with proper async conventions."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Status fields
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Relationships (lazy loading for async)
    wallets = relationship("Wallet", back_populates="user", lazy="select")
```

## 4. Transaction & Connection Management

### Repository Transaction Patterns

```python
async def update(self, entity: ExampleEntity, **kwargs) -> ExampleEntity:
    """Update entity with transaction management."""
    try:
        async with self.__database.get_session() as session:
            # Merge entity into current session
            entity = await session.merge(entity)

            # Apply updates
            for field, value in kwargs.items():
                if hasattr(entity, field):
                    setattr(entity, field, value)

            try:
                await session.commit()
            except IntegrityError as e:
                await session.rollback()
                self.__audit.error("update_integrity_error", error=str(e))
                raise

            await session.refresh(entity)
            return entity

    except Exception as e:
        self.__audit.error("update_failed", error=str(e))
        raise
```

### Bulk Operations

```python
from sqlalchemy import delete, update

async def delete_user_data(self, user_id: uuid.UUID) -> None:
    """Delete all user data in proper order."""
    async with self.__database.get_session() as session:
        # Delete related data first (foreign key constraints)
        await session.execute(
            delete(RefreshToken).where(RefreshToken.user_id == user_id)
        )
        await session.execute(
            delete(Wallet).where(Wallet.user_id == user_id)
        )

        # Delete user last
        await session.execute(
            delete(User).where(User.id == user_id)
        )

        await session.commit()
```

## 5. Migration Command Reference

### Common Migration Operations

```bash
# Create new migration
PYTHONPATH=. alembic revision --autogenerate -m "descriptive_message"

# Apply migrations
PYTHONPATH=. alembic upgrade head

# Rollback one migration
PYTHONPATH=. alembic downgrade -1

# Rollback to base
PYTHONPATH=. alembic downgrade base

# Show current revision
PYTHONPATH=. alembic current

# Show migration history
PYTHONPATH=. alembic history
```

### Makefile Integration

```bash
# Development workflow
make db-start          # Start database containers
make db-migrate        # Apply latest migrations
make test-quiet        # Run tests to verify

# Rolling back
make db-rollback       # Rollback one migration
make db-rollback-all   # Rollback to base
```

## 6. Complete Repository Example

```python
import uuid
import time
from typing import Optional, List
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError

from app.core.database import CoreDatabase
from app.models.wallet import Wallet
from app.utils.logging import Audit

class WalletRepository:
    """Repository for wallet persistence operations."""

    def __init__(self, database: CoreDatabase, audit: Audit):
        self.__database = database
        self.__audit = audit

    async def get_by_address(self, address: str) -> Optional[Wallet]:
        """Get wallet by address."""
        start_time = time.time()
        self.__audit.info("wallet_repository_get_by_address_started", address=address)

        try:
            async with self.__database.get_session() as session:
                stmt = select(Wallet).where(Wallet.address == address)
                result = await session.execute(stmt)
                wallet = result.scalar_one_or_none()

                duration = int((time.time() - start_time) * 1000)
                self.__audit.info(
                    "wallet_repository_get_by_address_success",
                    address=address,
                    found=wallet is not None,
                    duration_ms=duration,
                )
                return wallet

        except Exception as exc:
            duration = int((time.time() - start_time) * 1000)
            self.__audit.error(
                "wallet_repository_get_by_address_failed",
                address=address,
                duration_ms=duration,
                error=str(exc),
            )
            raise

    async def create(self, address: str, user_id: uuid.UUID, name: str = None) -> Wallet:
        """Create a new wallet."""
        self.__audit.info("wallet_repository_create_started", address=address, user_id=str(user_id))

        try:
            async with self.__database.get_session() as session:
                wallet = Wallet(
                    user_id=user_id,
                    address=address,
                    name=name or "Unnamed Wallet",
                    balance=0.0,
                )

                session.add(wallet)

                try:
                    await session.commit()
                except IntegrityError as e:
                    await session.rollback()
                    self.__audit.error("wallet_repository_create_integrity_error", error=str(e))
                    raise

                await session.refresh(wallet)

                self.__audit.info("wallet_repository_create_success", wallet_id=str(wallet.id))
                return wallet

        except Exception as e:
            self.__audit.error("wallet_repository_create_failed", error=str(e))
            raise

    async def get_by_user_id(self, user_id: uuid.UUID) -> List[Wallet]:
        """Get all wallets for a user."""
        self.__audit.info("wallet_repository_get_by_user_id_started", user_id=str(user_id))

        try:
            async with self.__database.get_session() as session:
                stmt = (
                    select(Wallet)
                    .where(Wallet.user_id == user_id)
                    .where(Wallet.is_active == True)
                    .order_by(Wallet.created_at.desc())
                )
                result = await session.execute(stmt)
                wallets = result.scalars().all()

                self.__audit.info(
                    "wallet_repository_get_by_user_id_success",
                    user_id=str(user_id),
                    wallet_count=len(wallets),
                )
                return wallets

        except Exception as e:
            self.__audit.error(
                "wallet_repository_get_by_user_id_failed",
                user_id=str(user_id),
                error=str(e),
            )
            raise
```

---

_This guide provides the essential database patterns used throughout the codebase. Follow these patterns for consistent, maintainable database operations._
