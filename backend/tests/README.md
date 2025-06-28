# Test Fixtures Architecture

This document describes the comprehensive fixture architecture for the test suite, designed to provide robust, modular, and performant testing infrastructure.

## 🗂️ Test Directory Structure

The tests are now organized under `backend/tests/` by backend/app modules and test types:

- **unit/**
  - adapters/
  - aggregators/
  - auth/
  - core/
  - domain/
  - usecase/
  - monitoring/
  - validators/
  - api/
  - storage/
  - schemas/
  - models/
  - repositories/
  - services/
  - tasks/
  - cli/
  - abi/
- **integration/**
  - adapters/
  - aggregators/
  - auth/
  - core/
  - domain/
  - usecase/
  - monitoring/
  - validators/
  - api/
  - storage/
  - schemas/
  - models/
  - repositories/
  - services/
  - tasks/
  - cli/
  - abi/
- **fixtures/** - shared fixture modules
- **utils/** - utility fixtures and helpers
- **plugins/** - pytest plugins for validation and templating
- **strategies/** - test strategy modules
- **property/** - property-based tests
- **performance/** - performance/load tests (skipped by default)
- **examples/** - code examples for testing patterns
- **templates/** - reusable test templates

Each module folder corresponds to the `backend/app/<module>/` directory. Place unit tests under `unit/<module>/`, integration tests under `integration/<module>/`. Shared infrastructure (fixtures, utils, etc.) remains at the top level.

## 🏗️ Architecture Overview

The fixture system is organized into a hierarchical module structure with clear separation of concerns:

```
backend/tests/fixtures/
├── __init__.py          # Package exports and documentation
├── base.py              # Foundation fixtures (engine, app, config)
├── database.py          # Database-specific fixtures with transactions
├── auth.py              # Authentication and user fixtures
├── client.py            # FastAPI TestClient fixtures
├── mocks.py             # External service mocking fixtures
└── config.py            # Fixture configuration and settings
```

## 📋 Fixture Categories

### 1. Base Fixtures (`base.py`)
Foundation fixtures that provide the core testing infrastructure:

- **`async_engine`** (session-scoped): Async database engine for the test session
- **`test_app`** (session-scoped): FastAPI application instance for testing

### 2. Database Fixtures (`database.py`)
Database-specific fixtures with proper transaction management:

- **`db_session`** (function-scoped): Async database session with automatic rollback
- **`module_db_session`** (module-scoped): Async session for shared test data
- **`sync_session`** (function-scoped): Sync database session with automatic rollback
- **`module_sync_session`** (module-scoped): Sync session for shared test data
- **`clean_db_session`** (function-scoped): Async session with automatic cleanup
- **`clean_sync_session`** (function-scoped): Sync session with automatic cleanup

### 3. Authentication Fixtures (`auth.py`)
User and authentication management fixtures:

- **`test_user`**: Basic test user with authentication
- **`test_user_with_wallet`**: Test user with associated wallet
- **`admin_user`**: Admin user with elevated privileges
- **`inactive_user`**: Inactive user for testing edge cases
- **`authenticated_client`**: Async client with user authentication
- **`admin_authenticated_client`**: Async client with admin authentication
- **`create_user_and_wallet`**: Factory for creating users with wallets
- **`create_multiple_users`**: Factory for creating multiple users
- **`create_user_with_tokens`**: Factory for creating users with multiple wallets

### 4. Client Fixtures (`client.py`)
FastAPI TestClient fixtures for endpoint testing:

- **`client`**: Basic test client without authentication
- **`async_client`**: Async test client without authentication
- **`client_with_db`**: Test client with database session override
- **`async_client_with_db`**: Async client with database session override
- **`authenticated_client`**: Test client with user authentication
- **`authenticated_async_client`**: Async client with user authentication

### 5. Mock Fixtures (`mocks.py`)
External service mocking fixtures:

- **`mock_redis`**: Mock Redis client
- **`mock_web3`**: Mock Web3 client for blockchain testing
- **`mock_httpx_client`**: Mock HTTPX client for external APIs
- **`mock_celery`**: Mock Celery for background tasks
- **`mock_s3_client`**: Mock S3 client for file storage
- **`mock_jwt_utils`**: Mock JWT utilities
- **`mock_password_hasher`**: Mock password hasher
- **`mock_external_apis`**: Comprehensive external API mocks
- **`mock_all_external_services`**: All external service mocks combined

### 6. Configuration Fixtures (`config.py`)
Test configuration and settings:

- **`test_config`** (session-scoped): Centralized test configuration
- **`mock_settings`** (autouse): Automatic environment mocking
- **`fixture_config`**: Function-scoped fixture configuration
- **`test_data_config`**: Test data generation configuration

## 🎯 Scoping Strategy

The fixture system implements a 3-tier scoping strategy for optimal performance:

### Session Scope (Expensive Setup)
- Database engines
- Application instances
- Global configuration

### Module Scope (Shared Data)
- Database sessions for shared test data
- Test data setup that can be reused across tests

### Function Scope (Test Isolation)
- Individual test data
- Mock objects
- Test clients
- Authentication contexts

## 🔧 Usage Examples

### Basic Test with Authentication
```python
import pytest

async def test_protected_endpoint(authenticated_client, test_user):
    response = await authenticated_client.get("/api/protected")
    assert response.status_code == 200
```

### Database Testing with Clean Session
```python
async def test_user_creation(clean_db_session):
    # Database is clean at start
    user = User(username="test", email="test@example.com")
    clean_db_session.add(user)
    await clean_db_session.commit()
    
    # Verify user was created
    result = await clean_db_session.get(User, user.id)
    assert result is not None
```

### Testing with External Service Mocks
```python
async def test_blockchain_integration(mock_web3, db_session):
    # Web3 is mocked, no real blockchain calls
    service = BlockchainService(db_session)
    balance = await service.get_wallet_balance("0x123...")
    assert balance == 1000000000000000000  # Mocked value
```

### Factory Pattern for Complex Data
```python
async def test_multiple_users(create_multiple_users):
    users = await create_multiple_users(5)
    assert len(users) == 5
    assert all(user.id is not None for user in users)
```

## 🚀 Performance Optimizations

### Transactional Rollbacks
All database fixtures use transactions with automatic rollback to ensure test isolation without the overhead of database recreation.

### Session-Scoped Expensive Operations
Database engines and application instances are created once per test session and reused across all tests.

### Mock External Services
External services are mocked by default to avoid network calls and external dependencies during testing.

## 🔒 Test Isolation

### Database Isolation
- Each test function gets a fresh database transaction
- Automatic rollback ensures no data persists between tests
- Module-scoped sessions available for shared data scenarios

### Authentication Isolation
- Each test gets unique user credentials
- JWT tokens are generated fresh for each test
- No shared authentication state between tests

### External Service Isolation
- All external services are mocked by default
- No real network calls during testing
- Predictable responses for consistent test results

## 📝 Best Practices

### Fixture Composition
```python
# Good: Compose fixtures for complex scenarios
async def test_complex_scenario(
    clean_db_session,
    test_user_with_wallet,
    authenticated_async_client,
    mock_external_apis
):
    # Test implementation
    pass
```

### Scoping Considerations
```python
# Use function scope for test isolation
@pytest_asyncio.fixture
async def test_user(db_session):  # function-scoped
    # Creates unique user for each test
    pass

# Use module scope for shared expensive data
@pytest_asyncio.fixture(scope="module")
async def shared_test_data(module_db_session):  # module-scoped
    # Creates data shared across module tests
    pass
```

### Mock Usage
```python
# Use specific mocks for targeted testing
async def test_redis_operations(mock_redis):
    # Test Redis-specific functionality
    pass

# Use comprehensive mocks for integration testing
async def test_full_integration(mock_all_external_services):
    # Test with all external services mocked
    pass
```

## 🔄 Migration Guide

### From Old Fixtures
If you have existing tests using old fixtures, you can gradually migrate:

1. **Replace direct imports** with new fixture imports
2. **Update fixture names** to match new naming conventions
3. **Add proper scoping** where needed
4. **Use composition** for complex scenarios

### Example Migration
```python
# Old way
from tests.conftest import db_session, test_user

# New way
from tests.fixtures import db_session, test_user
# or
from tests.fixtures.database import db_session
from tests.fixtures.auth import test_user
```

## 🧪 Testing the Fixtures

The fixtures themselves are tested to ensure they work correctly:

```bash
# Run fixture tests
pytest tests/unit/fixtures/ -v

# Run integration tests with fixtures
pytest tests/integration/ -v

# Run all tests to verify fixture compatibility
pytest --tb=short
```

## 📚 Additional Resources

- [Pytest Fixture Documentation](https://docs.pytest.org/en/stable/explanation/fixtures.html)
- [Pytest-Asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing Patterns](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)

## 🔍 Example Test Patterns

Explore practical examples in the `backend/tests/examples` directory:

- `examples/basic/`: Simple patterns (authentication, database, API)
- `examples/api/`: Endpoint testing examples (error handling, mocking)
- `examples/integration/`: Complex workflow examples (end-to-end, performance)
- `examples/templates/`: Reusable test templates for quick scaffolding

Refer to each subdirectory's README for detailed usage and code snippets. 