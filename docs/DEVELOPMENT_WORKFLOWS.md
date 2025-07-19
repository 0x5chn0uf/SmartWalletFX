# Development Workflows

> **Audience**: Claude Code & contributors  
> **Focus**: Practical development workflows for adding features, migrations, tests, and debugging

This document provides step-by-step workflows for common development tasks in the SmartWalletFX backend.

## 1. Adding New Domains/Features

### Domain Structure Analysis

The codebase follows a clear domain-driven structure:

```
app/
├── domain/
│   ├── schemas/          # Pydantic models for validation
│   └── interfaces/       # Repository interfaces
├── models/              # SQLAlchemy ORM models
├── repositories/        # Data access layer
├── usecase/            # Business logic layer
├── api/endpoints/      # HTTP endpoint controllers
└── services/           # External service integrations
```

### Workflow: Adding a New Domain

**Step 1**: Create domain schemas

```python
# app/domain/schemas/my_feature.py
from pydantic import BaseModel
from typing import Optional
import uuid

class MyFeatureCreate(BaseModel):
    name: str
    description: Optional[str] = None

class MyFeatureResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    created_at: datetime
```

**Step 2**: Create SQLAlchemy model

```python
# app/models/my_feature.py
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class MyFeature(Base):
    __tablename__ = "my_features"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Step 3**: Create repository

```python
# app/repositories/my_feature_repository.py
from app.core.database import CoreDatabase
from app.models.my_feature import MyFeature
from app.utils.logging import Audit

class MyFeatureRepository:
    def __init__(self, database: CoreDatabase, audit: Audit):
        self.__database = database
        self.__audit = audit

    async def create(self, feature: MyFeature) -> MyFeature:
        async with self.__database.get_session() as session:
            session.add(feature)
            await session.commit()
            await session.refresh(feature)
            self.__audit.info("my_feature_created", feature_id=str(feature.id))
            return feature
```

**Step 4**: Create usecase

```python
# app/usecase/my_feature_usecase.py
from app.repositories.my_feature_repository import MyFeatureRepository
from app.domain.schemas.my_feature import MyFeatureCreate, MyFeatureResponse

class MyFeatureUsecase:
    def __init__(self, repo: MyFeatureRepository, config: Configuration, audit: Audit):
        self.__repo = repo
        self.__config = config
        self.__audit = audit

    async def create_feature(self, data: MyFeatureCreate) -> MyFeatureResponse:
        feature = MyFeature(name=data.name, description=data.description)
        created = await self.__repo.create(feature)
        return MyFeatureResponse.model_validate(created)
```

**Step 5**: Create endpoint

```python
# app/api/endpoints/my_feature.py
from fastapi import APIRouter
from app.usecase.my_feature_usecase import MyFeatureUsecase

class MyFeature:
    ep = APIRouter(tags=["my-feature"])

    def __init__(self, usecase: MyFeatureUsecase):
        self.__usecase = usecase
        self.ep.add_api_route("/my-features", self.create_feature, methods=["POST"])

    async def create_feature(self, data: MyFeatureCreate):
        return await self.__usecase.create_feature(data)
```

**Step 6**: Register in DI Container

```python
# app/di.py - Add to appropriate sections
def _initialize_repositories(self):
    # ... existing repositories
    my_feature_repo = MyFeatureRepository(database, audit)
    self.register_repository("my_feature", my_feature_repo)

def _initialize_usecases(self):
    # ... existing usecases
    my_feature_uc = MyFeatureUsecase(
        self.get_repository("my_feature"),
        self.get_core("config"),
        self.get_core("audit")
    )
    self.register_usecase("my_feature", my_feature_uc)

def _initialize_endpoints(self):
    # ... existing endpoints
    my_feature_endpoint = MyFeature(self.get_usecase("my_feature"))
    self.register_endpoint("my_feature", my_feature_endpoint)
```

## 2. Migration Creation Workflow

### Analyzing Existing Migrations

```bash
# List all migrations
ls migrations/versions/

# Example migration naming pattern:
0001_init.py                 # Initial schema
0002_add_portfolio_snapshot_cache_table.py
0003_rename_password_hash_to_hashed_password.py
0011_add_password_reset_table.py
0012_add_oauth_accounts_table.py
```

### Workflow: Creating a Migration

**Step 1**: Generate migration

```bash
cd backend
alembic revision --autogenerate -m "add my_feature table"
```

**Step 2**: Review generated migration

```python
# migrations/versions/XXXX_add_my_feature_table.py
def upgrade() -> None:
    op.create_table(
        'my_features',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_my_features_name', 'my_features', ['name'])

def downgrade() -> None:
    op.drop_index('ix_my_features_name', 'my_features')
    op.drop_table('my_features')
```

**Step 3**: Apply migration

```bash
alembic upgrade head
```

**Step 4**: Verify schema

```bash
# Connect to database and verify table creation
psql -d smartwallet_dev -c "\dt my_features"
```

## 3. Test Writing Patterns

### Test Structure Analysis

```
tests/
├── domains/              # Domain-specific tests
│   ├── auth/
│   │   ├── unit/        # Unit tests with mocks
│   │   └── integration/ # Integration tests with database
│   └── wallets/
├── infrastructure/       # Infrastructure tests
└── shared/fixtures/     # Shared test fixtures
```

### Unit Test Pattern

```python
# tests/domains/my_feature/unit/test_my_feature_usecase.py
import pytest
from unittest.mock import AsyncMock, Mock
from app.usecase.my_feature_usecase import MyFeatureUsecase

@pytest.fixture
def mock_my_feature_repository():
    mock_repo = Mock()
    mock_repo.create = AsyncMock()
    mock_repo.get_by_id = AsyncMock()
    return mock_repo

@pytest.fixture
def my_feature_usecase(mock_my_feature_repository, mock_config, mock_audit):
    return MyFeatureUsecase(
        repo=mock_my_feature_repository,
        config=mock_config,
        audit=mock_audit
    )

@pytest.mark.asyncio
async def test_create_feature_success(my_feature_usecase, mock_my_feature_repository):
    # Arrange
    create_data = MyFeatureCreate(name="Test Feature")
    mock_feature = Mock(id=uuid.uuid4(), name="Test Feature")
    mock_my_feature_repository.create.return_value = mock_feature

    # Act
    result = await my_feature_usecase.create_feature(create_data)

    # Assert
    assert result.name == "Test Feature"
    mock_my_feature_repository.create.assert_called_once()
```

### Integration Test Pattern

```python
# tests/domains/my_feature/integration/test_my_feature_flow.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_feature_endpoint(integration_async_client: AsyncClient):
    # Arrange
    feature_data = {"name": "Integration Test Feature"}

    # Act
    response = await integration_async_client.post(
        "/my-features",
        json=feature_data
    )

    # Assert
    assert response.status_code == 201
    result = response.json()
    assert result["name"] == "Integration Test Feature"
    assert "id" in result
```

### Running Tests

```bash
# Run all tests quietly (Claude's preferred mode)
make test-quiet

# Run specific test file
pytest -q --tb=short --color=no tests/domains/my_feature/unit/test_my_feature_usecase.py

# Run tests with pattern matching
pytest -q --tb=short --color=no -k "test_create_feature"

# Run integration tests only
pytest -q --tb=short --color=no tests/domains/my_feature/integration/
```

## 4. Debugging Strategies

### Using DI Container for Debugging

```python
# Access any component through DI container
from app.di import DIContainer

di = DIContainer()
config = di.get_core("config")
user_repo = di.get_repository("user")
auth_usecase = di.get_usecase("auth")

# Test individual components
user = await user_repo.get_by_id(user_id)
```

### Database Debugging

```bash
# Connect to development database
psql -h postgres-dev -U devuser -d smartwallet_dev

# Check recent migrations
SELECT version_num FROM alembic_version;

# Inspect table structure
\d+ users
\d+ wallets
```

### Logging and Audit Trail

```python
# Enable debug logging in development
LOG_LEVEL=DEBUG

# Audit logs provide structured debugging info
self.__audit.info("operation_start", user_id=str(user.id), operation="create_wallet")
self.__audit.error("operation_failed", error=str(e), context={"user_id": str(user.id)})
```

### Testing Database Queries

```python
# Use test database session for query debugging
from tests.shared.fixtures.database import db_session

async with db_session() as session:
    result = await session.execute(
        select(User).where(User.email == "test@example.com")
    )
    user = result.scalar_one_or_none()
```

## Key Development Principles

1. **Follow the Layer Pattern**: Domain → Model → Repository → Usecase → Endpoint
2. **Use DI Container**: Register all new components in the dependency injection container
3. **Test Early**: Write unit tests for business logic, integration tests for flows
4. **Audit Everything**: Add audit logging for all significant operations
5. **Validate Input**: Use Pydantic schemas for all API inputs and outputs
6. **Handle Errors**: Use the centralized error handling for consistent responses

## Common Debugging Commands

```bash
# Check application logs
docker-compose logs backend

# Database connection test
make db-test

# Run linting and formatting
make lint
make format

# Generate test coverage report
make test-cov

# Check for security issues
make bandit
make safety
```

---

_Last updated: 19 July 2025_
