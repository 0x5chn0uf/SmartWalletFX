# Testing Guide - Enhanced Test Infrastructure

This guide covers the enhanced testing infrastructure implemented for better test isolation, performance, and reliability.

## Table of Contents

1. [Overview](#overview)
2. [Test Architecture](#test-architecture)
3. [Test Categories](#test-categories)
5. [Docker Test Infrastructure](#docker-test-infrastructure)
6. [Writing Tests](#writing-tests)
7. [Running Tests](#running-tests)
8. [CI/CD Integration](#cicd-integration)
9. [Best Practices](#best-practices)
10. [Migration Guide](#migration-guide)

## Overview

Our testing infrastructure provides multiple layers of testing with different levels of isolation and realism:

- **Unit Tests**: Fast, isolated tests with mocks (SQLite in-memory)
- **Integration Tests**: Real database interactions with Docker containers
- **Performance Tests**: Benchmarking and performance regression testing
- **E2E Tests**: Full system testing with external services

### Key Benefits

- ⚡ **52x faster unit tests** with optimized configurations
- 🐳 **Docker-based integration testing** with isolated services
- 🎭 **Sophisticated mocking** with realistic failure scenarios
- 🔧 **Flexible DI container** system for different test types
- 📊 **Comprehensive coverage** with parallel execution

## Test Architecture

```
tests/
├── domains/                 # Domain-driven test organization
│   ├── auth/
│   │   ├── unit/           # Fast, isolated tests
│   │   ├── integration/    # Database integration tests
│   │   └── property/       # Property-based tests
│   ├── users/
│   ├── wallets/
│   └── ...
├── infrastructure/         # Infrastructure concerns
│   ├── api/               # API layer tests
│   ├── database/          # Database layer tests
│   └── security/          # Security tests
└── shared/                # Shared test utilities
    ├── fixtures/          # Test fixtures and mocks
    │   ├── test_di_container.py # Test DI container
    │   ├── test_config.py       # Test configurations
    │   └── test_database.py     # Database test utilities
    └── utils/             # Test utilities
```

## Test Categories

### Unit Tests
Fast, isolated tests that rely on simple mocks for external dependencies.

```python
# tests/domains/auth/unit/test_auth_service.py
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_login_success(auth_service, mock_user_repository):
    """Test successful user login with simple mocks."""
    mock_user_repository.get_by_email = AsyncMock(return_value=test_user)
    mock_user_repository.verify_password = AsyncMock(return_value=True)

    result = await auth_service.login("test@example.com", "password")

    mock_user_repository.get_by_email.assert_called_once_with("test@example.com")
    assert result.access_token is not None
```

### Integration Tests
Tests that use real database connections and verify actual data persistence.

```python
# tests/domains/auth/integration/test_auth_flow.py
import pytest

@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_auth_flow(
    test_di_container_with_db,
    integration_test_session
):
    """Test complete authentication flow with real database."""
    auth_usecase = test_di_container_with_db.get_usecase("auth")
    
    # Register user
    user = await auth_usecase.register(UserCreate(
        username="testuser",
        email="test@example.com", 
        password="StrongPassword123!"
    ))
    
    # Verify user exists in database
    saved_user = await integration_test_session.get(User, user.id)
    assert saved_user.email == "test@example.com"
```



## Docker Test Infrastructure

### Test Services

The Docker test infrastructure provides isolated services:

```yaml
# docker-compose.test.yml (automatically managed)
services:
  postgres-test:    # Port 55433 (isolated from dev)
  redis-test:       # Port 6380 (isolated from dev)
  backend-test:     # Port 8001 (for integration testing)
```

### Usage

```bash
# Start test infrastructure
make test-docker-up

# Run integration tests with Docker
make test-integration-docker

# Clean up test infrastructure
make test-docker-clean
```

### Configuration

```python
# Integration test configuration
from tests.shared.fixtures.test_config import create_integration_test_config

config = create_integration_test_config(
    test_db_url="postgresql+asyncpg://testuser:testpass@localhost:55433/test_smartwallet"
)
```

## Writing Tests

### Test Naming Conventions

```python
# Unit tests
def test_login_success()                    # Happy path
def test_login_invalid_credentials()        # Error case
def test_login_rate_limited()              # Edge case

# Integration tests  
def test_auth_flow_end_to_end()            # Full workflow
def test_database_constraints()            # Database-specific

# Performance tests
def test_login_performance()               # Benchmarking
```

### Fixture Usage

```python
# Use specific fixtures for different test types
@pytest.mark.asyncio
async def test_unit_with_mocks(
    test_di_container_unit,           # Unit test DI container
    mock_user_repository,             # Simple mock
    mock_config                       # Mock configuration
):
    pass

@pytest.mark.asyncio  
async def test_integration_with_db(
    test_di_container_with_db,        # Integration DI container
    integration_test_session,         # Real database session
    test_database_config              # Integration configuration
):
    pass
```

### Test Data Management

```python
# Use factories for consistent test data
from tests.shared.fixtures.factories import UserFactory, WalletFactory

@pytest.fixture
def test_user():
    return UserFactory.build(
        username="testuser",
        email="test@example.com"
    )

@pytest.fixture 
def test_wallet(test_user):
    return WalletFactory.build(
        user_id=test_user.id,
        address="0x1234..."
    )
```

## Running Tests

### Local Development

```bash
# Fast unit tests (recommended for development)
make test-unit
# Complete unit and integration tests
# Integration tests with Docker
make test-integration-docker

# Performance tests
make test-profile

# Complete test suite
make test-all-scenarios
```

### Environment Variables

```bash
# Test type selection
export TEST_TYPE=unit|integration|performance

# Database configuration
export TEST_DB_URL="postgresql+asyncpg://testuser:testpass@localhost:55433/test_smartwallet"

# Performance optimization
export BCRYPT_ROUNDS=4

# Docker usage
export USE_DOCKER_TESTS=true
```

### IDE Integration

For VS Code, add to `.vscode/settings.json`:

```json
{
    "python.testing.pytestArgs": [
        "tests",
        "--tb=short",
        "--cov=app",
        "--cov-report=term-missing"
    ],
    "python.testing.unittestEnabled": false,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestPath": "pytest"
}
```

## CI/CD Integration

### GitHub Actions Workflow

The enhanced CI/CD pipeline provides:

- **Parallel test execution** across multiple domains
- **Matrix testing** for different test groups
- **Docker integration** for realistic testing
- **Performance benchmarking** 
- **Coverage reporting** with Codecov

### Pipeline Stages

1. **Security & Quality** (10 min) - Bandit, Safety, Ruff, MyPy
2. **Unit Tests** (15 min) - Parallel execution by domain
3. **Integration Tests** (30 min) - Real database testing
4. **Performance Tests** (20 min) - Benchmarking
5. **Docker Integration** (25 min) - Full system testing

### Branch Protection

Configure branch protection with required status checks:

- `Security & Quality Checks`
- `Unit Tests (auth, users, wallets, tokens, email, oauth)`
- `Integration Tests`
- `Docker Integration Test`

## Best Practices

### 1. Test Organization

```python
class TestUserAuthentication:
    """Group related tests in classes."""
    
    @pytest.mark.asyncio
    async def test_login_success(self):
        """Test successful login scenario."""
        pass
        
    @pytest.mark.asyncio  
    async def test_login_failure(self):
        """Test failed login scenario."""
        pass
```

## Migration Guide

### From Basic Tests to Integration Tests

**Before:**
```python
def test_basic(mock_db):
    # All mocked
    pass
```

**After:**
```python
@pytest.mark.integration
async def test_integration(
    test_di_container_with_db,
    integration_test_session
):
    # Real database operations
    result = await real_service.create_user(user_data)
    
    # Verify in database
    saved_user = await integration_test_session.get(User, result.id)
    assert saved_user.email == user_data.email
```

### Updating CI/CD

2. **Update branch protection** rules
3. **Configure environment variables**
4. **Set up Codecov integration**

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all fixture imports are correct
2. **Mock Configuration**: Verify mock behaviors are set before test execution
3. **Database Issues**: Check Docker services are running for integration tests
4. **Performance**: Use unit tests for fast feedback, integration for verification

### Debug Commands

```bash
# Check Docker test services
docker-compose -f docker-compose.test.yml ps

# Verify test database connection  
TEST_DB_URL="postgresql+asyncpg://testuser:testpass@localhost:55433/test_smartwallet" \
python -c "from sqlalchemy import create_engine; print('Connection OK')"

# Run single test with verbose output
pytest tests/path/to/test.py::test_function -v -s --tb=long
```

---

This enhanced testing infrastructure provides a solid foundation for reliable, fast, and comprehensive testing. Follow these patterns for consistent, maintainable tests that provide confidence in code quality and system reliability. 