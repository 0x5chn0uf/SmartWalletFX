# Testing Guide - Enhanced Test Infrastructure

This guide covers the enhanced testing infrastructure implemented for better test isolation, performance, and reliability.

## Table of Contents

1. [Overview](#overview)
2. [Test Architecture](#test-architecture)
3. [Test Categories](#test-categories)
4. [Enhanced Mock System](#enhanced-mock-system)
5. [Docker Test Infrastructure](#docker-test-infrastructure)
6. [Writing Tests](#writing-tests)
7. [Running Tests](#running-tests)
8. [CI/CD Integration](#cicd-integration)
9. [Best Practices](#best-practices)
10. [Migration Guide](#migration-guide)

## Overview

Our testing infrastructure provides multiple layers of testing with different levels of isolation and realism:

- **Unit Tests**: Fast, isolated tests with enhanced mocking (SQLite in-memory)
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
    │   ├── enhanced_mocks.py    # Enhanced mock system
    │   ├── test_di_container.py # Test DI container
    │   ├── test_config.py       # Test configurations
    │   └── test_database.py     # Database test utilities
    └── utils/             # Test utilities
```

## Test Categories

### Unit Tests
Fast, isolated tests that use mocks for all external dependencies.

```python
# tests/domains/auth/unit/test_auth_service.py
import pytest
from tests.shared.fixtures.enhanced_mocks import MockBehavior

@pytest.mark.asyncio
async def test_login_success(
    auth_service,
    mock_user_repository_enhanced,
    mock_assertions
):
    """Test successful user login with enhanced mocks."""
    # Configure realistic mock behavior
    mock_user_repository_enhanced.configure_repository_mock(
        "user",
        get_by_email=AsyncMock(return_value=test_user),
        verify_password=AsyncMock(return_value=True)
    )
    
    result = await auth_service.login("test@example.com", "password")
    
    # Use enhanced assertions
    mock_assertions.assert_called_once_with(
        mock_user_repository_enhanced, "get_by_email", "test@example.com"
    )
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

## Enhanced Mock System

The enhanced mock system provides realistic behaviors and comprehensive tracking.

### Basic Mock Usage

```python
from tests.shared.fixtures.enhanced_mocks import (
    MockBehavior, 
    MockAssertions,
    MockServiceFactory
)

# Create mocks with specific behaviors
user_repo = MockServiceFactory.create_user_repository(MockBehavior.SUCCESS)
email_service = MockServiceFactory.create_email_service(MockBehavior.SLOW_RESPONSE)
failing_service = MockServiceFactory.create_file_upload_service(MockBehavior.FAILURE)
```

### Mock Behaviors

```python
class MockBehavior(Enum):
    SUCCESS = "success"          # Normal operation
    FAILURE = "failure"          # Service failures
    TIMEOUT = "timeout"          # Network timeouts
    RATE_LIMITED = "rate_limited"    # Rate limiting
    SLOW_RESPONSE = "slow_response"  # Performance issues
```

### Stateful Mocks

Enhanced mocks maintain state and track calls:

```python
@pytest.mark.asyncio
async def test_user_creation_tracking(mock_user_repository_enhanced):
    """Test user creation with call tracking."""
    
    # Create users
    await mock_user_repository_enhanced.create(user1_data)
    await mock_user_repository_enhanced.create(user2_data)
    
    # Verify call history
    create_calls = mock_user_repository_enhanced.get_calls("create")
    assert len(create_calls) == 2
    
    # Check internal state
    assert len(mock_user_repository_enhanced.users) == 2
    
    # Test duplicate email validation
    with pytest.raises(ValueError, match="Email already exists"):
        await mock_user_repository_enhanced.create(duplicate_email_data)
```

### Failure Scenario Testing

```python
@pytest.mark.asyncio
async def test_email_service_failure_handling(
    email_verification_usecase,
    failing_email_service
):
    """Test handling of email service failures."""
    
    # Configure failure behavior
    failing_email_service.set_behavior(MockBehavior.FAILURE)
    
    # Test error handling
    result = await email_verification_usecase.send_verification_email(
        "test@example.com"
    )
    
    # Should handle failure gracefully
    assert result.success is False
    assert result.retry_after is not None
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
    mock_user_repository_enhanced,    # Enhanced mock
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

# All tests with enhanced mocking
make test-enhanced

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

### 2. Mock Configuration

```python
# Configure mocks explicitly
mock_service.configure_repository_mock(
    "user",
    get_by_email=AsyncMock(return_value=test_user),
    create=AsyncMock(side_effect=create_user_side_effect)
)

# Use behavior-specific fixtures
def test_with_failing_service(failing_email_service):
    failing_email_service.set_behavior(MockBehavior.TIMEOUT)
```

### 3. Assertion Patterns

```python
# Use enhanced assertions
mock_assertions.assert_called_once_with(
    mock_service, "method_name", expected_arg
)

# Verify state changes
assert len(mock_service.get_calls("create")) == 2
assert mock_service.users["user_id"].email == "new@email.com"
```

### 4. Error Testing

```python
# Test all error scenarios
@pytest.mark.parametrize("behavior,expected_error", [
    (MockBehavior.FAILURE, ServiceError),
    (MockBehavior.TIMEOUT, TimeoutError),
    (MockBehavior.RATE_LIMITED, RateLimitError),
])
async def test_error_scenarios(behavior, expected_error, mock_service):
    mock_service.set_behavior(behavior)
    
    with pytest.raises(expected_error):
        await service_under_test.perform_operation()
```

## Migration Guide

### From Old Mocks to Enhanced Mocks

**Before:**
```python
def test_old_style(mock_user_repo):
    mock_user_repo.get_by_id.return_value = user
    mock_user_repo.create.return_value = user
    
    # Test logic
    
    mock_user_repo.get_by_id.assert_called_once_with(user_id)
```

**After:**
```python
def test_enhanced_style(
    mock_user_repository_enhanced, 
    mock_assertions
):
    # Configure realistic behavior
    mock_user_repository_enhanced.configure_repository_mock(
        "user",
        get_by_id=AsyncMock(return_value=user),
        create=AsyncMock(return_value=user)
    )
    
    # Test logic
    
    # Enhanced assertions with call tracking
    mock_assertions.assert_called_once_with(
        mock_user_repository_enhanced, "get_by_id", user_id
    )
    
    # Verify state
    assert len(mock_user_repository_enhanced.users) == 1
```

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

1. **Replace old workflow** with `test-enhanced.yml`
2. **Update branch protection** rules
3. **Configure environment variables**
4. **Set up Codecov integration**

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all enhanced fixture imports are correct
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