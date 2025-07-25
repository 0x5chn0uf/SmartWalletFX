# Testing Migration Guide

This guide provides step-by-step instructions for migrating existing tests to use the enhanced testing infrastructure.

## Quick Migration Checklist

- [ ] Update imports to include enhanced mocks
- [ ] Replace basic Mock objects with enhanced mocks
- [ ] Add proper test markers (`@pytest.mark.integration`, etc.)
- [ ] Update fixture usage to use new DI containers
- [ ] Convert assertions to use enhanced assertion helpers
- [ ] Add failure scenario testing

## Step-by-Step Migration

### 1. Update Imports

**Before:**
```python
from unittest.mock import Mock, AsyncMock, patch
import pytest
```

**After:**
```python
from unittest.mock import Mock, AsyncMock, patch
import pytest
from tests.shared.fixtures.enhanced_mocks import MockBehavior
from tests.shared.fixtures.enhanced_mocks.assertions import MockAssertions
```

### 2. Replace Basic Mocks with Enhanced Mocks

**Before:**
```python
def test_user_creation(mock_user_repo):
    mock_user_repo.create.return_value = user
    mock_user_repo.get_by_email.return_value = None
    
    result = service.create_user(user_data)
    
    mock_user_repo.create.assert_called_once()
```

**After:**
```python
def test_user_creation(
    mock_user_repository_enhanced,
    mock_assertions
):
    # Configure enhanced mock with realistic behavior
    mock_user_repository_enhanced.configure_repository_mock(
        "user",
        create=AsyncMock(return_value=user),
        get_by_email=AsyncMock(return_value=None)
    )
    
    result = await service.create_user(user_data)
    
    # Use enhanced assertions
    mock_assertions.assert_called_once_with(
        mock_user_repository_enhanced, "create", user_data
    )
    
    # Verify internal state
    assert len(mock_user_repository_enhanced.users) == 1
```

### 3. Add Test Markers

**Before:**
```python
def test_integration_flow():
    # Test that uses database
    pass
```

**After:**
```python
@pytest.mark.integration
def test_integration_flow():
    # Test that uses database
    pass
```

### 4. Update Fixture Usage

**Before:**
```python
def test_with_old_fixtures(db_session, mock_user_repo):
    pass
```

**After:**
```python
# For unit tests
def test_unit_with_enhanced_fixtures(
    test_di_container_unit,
    mock_user_repository_enhanced
):
    pass

# For integration tests  
@pytest.mark.integration
def test_integration_with_enhanced_fixtures(
    test_di_container_with_db,
    integration_test_session
):
    pass
```

### 5. Add Failure Scenario Testing

**Before:**
```python
def test_success_case():
    # Only tests happy path
    pass
```

**After:**
```python
def test_success_case(mock_service_enhanced):
    # Happy path with enhanced mock
    pass

def test_failure_scenarios(
    failing_user_repository,  # Behavior-specific fixture
    mock_assertions
):
    # Test failure handling
    failing_user_repository.set_behavior(MockBehavior.FAILURE)
    
    with pytest.raises(ServiceError):
        await service.create_user(user_data)
        
    # Verify error was tracked
    failed_calls = failing_user_repository.get_calls("create")
    assert len(failed_calls) == 1
    assert failed_calls[0].exception is not None
```

## Common Migration Patterns

### Repository Tests

**Before:**
```python
@pytest.mark.asyncio
async def test_user_repository_create(mock_session):
    mock_session.add.return_value = None
    mock_session.commit.return_value = None
    
    repo = UserRepository(mock_session)
    result = await repo.create(user_data)
    
    mock_session.add.assert_called_once()
```

**After:**
```python
@pytest.mark.asyncio
async def test_user_repository_create(
    mock_user_repository_enhanced,
    mock_assertions
):
    # Test with realistic repository behavior
    result = await mock_user_repository_enhanced.create(user_data)
    
    # Verify call and state
    mock_assertions.assert_called_once_with(
        mock_user_repository_enhanced, "create", user_data
    )
    assert result.username == user_data.username
    assert len(mock_user_repository_enhanced.users) == 1
```

### Service Tests

**Before:**
```python
def test_email_service(mock_smtp):
    mock_smtp.send.return_value = True
    
    service = EmailService(mock_smtp)
    result = service.send_email("test@example.com", "subject", "body")
    
    assert result is True
```

**After:**
```python
def test_email_service_success(
    mock_email_service_enhanced,
    mock_assertions
):
    result = await mock_email_service_enhanced.send_verification_email(
        "test@example.com", "token123"
    )
    
    assert result is True
    
    # Verify email was tracked
    sent_emails = mock_email_service_enhanced.get_sent_emails("verification")
    assert len(sent_emails) == 1
    assert sent_emails[0]["to"] == "test@example.com"

def test_email_service_failure(slow_email_service):
    slow_email_service.set_behavior(MockBehavior.FAILURE)
    
    result = await slow_email_service.send_verification_email(
        "test@example.com", "token123"
    )
    
    assert result is False
```

### Endpoint Tests

**Before:**
```python
async def test_endpoint(mock_usecase):
    mock_usecase.process.return_value = result
    
    endpoint = UserEndpoint(mock_usecase)
    response = await endpoint.create_user(request, user_data)
    
    assert response.status_code == 201
```

**After:**
```python
async def test_endpoint_success(
    users_endpoint_with_di,
    mock_user_repository_enhanced,
    mock_assertions
):
    # Configure realistic mock behavior
    mock_user_repository_enhanced.configure_repository_mock(
        "user",
        create=AsyncMock(return_value=created_user)
    )
    
    response = await users_endpoint_with_di.create_user(request, user_data)
    
    assert response.status_code == 201
    mock_assertions.assert_called_once_with(
        mock_user_repository_enhanced, "create", user_data
    )

async def test_endpoint_validation_error(
    users_endpoint_with_di,
    failing_user_repository
):
    failing_user_repository.set_behavior(MockBehavior.FAILURE)
    
    with pytest.raises(HTTPException) as exc_info:
        await users_endpoint_with_di.create_user(request, invalid_data)
    
    assert exc_info.value.status_code == 400
```

## Integration Test Migration

### From Mock-Heavy to Real Database

**Before:**
```python
def test_auth_flow(mock_user_repo, mock_jwt, mock_email):
    # Everything mocked
    mock_user_repo.create.return_value = user
    mock_jwt.create_token.return_value = "token"
    mock_email.send.return_value = True
    
    # Test logic with all mocks
```

**After:**
```python
@pytest.mark.integration
async def test_auth_flow_integration(
    test_di_container_with_db,
    integration_test_session
):
    # Use real database and services
    auth_usecase = test_di_container_with_db.get_usecase("auth")
    
    # Register user - real database operation
    user = await auth_usecase.register(user_data)
    
    # Verify user exists in database
    saved_user = await integration_test_session.get(User, user.id)
    assert saved_user.email == user_data.email
    
    # Login - real JWT generation
    tokens = await auth_usecase.login(user_data.email, user_data.password)
    assert tokens.access_token is not None
```

## Docker Integration Migration

### Adding Docker Tests

**Before:**
```python
# No Docker integration
```

**After:**
```python
# Add to conftest.py or specific test file
@pytest.mark.integration
class TestDockerIntegration:
    """Tests that require Docker services."""
    
    async def test_full_system_integration(self):
        """Test with real PostgreSQL and Redis via Docker."""
        # This test will use docker-compose.test.yml services
        pass
```

### Environment Configuration

**Before:**
```python
# Manual configuration
DATABASE_URL = "sqlite:///test.db"
```

**After:**
```python
# Use test configuration classes
from tests.shared.fixtures.test_config import create_integration_test_config

config = create_integration_test_config(
    test_db_url=os.getenv("TEST_DB_URL")
)
```

## CI/CD Migration

### Update GitHub Actions

**Before:**
```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Setup Python
      uses: actions/setup-python@v2
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run tests
      run: pytest tests/
```

**After:**
```yaml
# Use the enhanced workflow
# Copy .github/workflows/test-enhanced.yml and customize as needed
```

### Update Branch Protection

1. Go to GitHub repository settings
2. Navigate to "Branches"
3. Edit branch protection for `main`
4. Update required status checks:
   - `Security & Quality Checks`
   - `Unit Tests (auth)`
   - `Unit Tests (users)`
   - `Unit Tests (wallets)`
   - `Integration Tests`
   - `Docker Integration Test`

## Testing Commands Migration

### Local Development

**Before:**
```bash
pytest tests/
pytest tests/ --cov=app
```

**After:**
```bash
# Fast unit tests (recommended for development)
make test-unit

# Enhanced mocking
make test-enhanced  

# Integration with Docker
make test-integration-docker

# Full test suite
make test-all-scenarios
```

## Validation and Verification

### After Migration Checklist

1. **Run all test categories:**
   ```bash
   make test-unit          # Should be fast (< 30s)
   make test-integration   # Should work with Docker
   make test-enhanced      # Should use new mocks
   ```

2. **Verify test markers:**
   ```bash
   pytest --markers        # Should show integration, performance, etc.
   ```

3. **Check coverage:**
   ```bash
   make test-cov          # Should maintain or improve coverage
   ```

4. **Validate Docker integration:**
   ```bash
   make test-docker-up    # Should start services
   make test-docker-down  # Should clean up
   ```

### Common Issues and Solutions

**Issue: Import errors after migration**
```python
# Solution: Update imports
from tests.shared.fixtures.enhanced_mocks import MockBehavior
```

**Issue: Fixture not found**
```python
# Solution: Use correct fixture names
def test_example(mock_user_repository_enhanced):  # Not mock_user_repository
```

**Issue: Integration tests failing**
```bash
# Solution: Ensure Docker services are running
make test-docker-up
```

**Issue: Performance regression**
```bash
# Solution: Use unit tests for fast feedback
make test-unit  # Should be under 30 seconds
```

## Support and Resources

- **Testing Guide**: See `docs/TESTING_GUIDE.md` for comprehensive documentation
- **Example Tests**: Look at migrated tests in `tests/domains/*/unit/`
- **Docker Setup**: See `docker-compose.test.yml` for infrastructure
- **CI/CD**: See `.github/workflows/test-enhanced.yml` for pipeline

---

Follow this migration guide step-by-step to transition your tests to the enhanced infrastructure. The new system provides better reliability, performance, and debugging capabilities while maintaining comprehensive test coverage. 