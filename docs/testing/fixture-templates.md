# Fixture Templates

This document provides documentation and usage examples for the reusable test templates available in `backend/tests/examples/templates`.

## API Test Template

File: `backend/tests/examples/templates/api_test_template.py`

Usage:
```python
from tests.examples.templates.api_test_template import APITestConfig, get_api_fixtures

config = APITestConfig(async_mode=True, authenticated=True, use_db=True, mock_http=True)
fixtures = get_api_fixtures(config)

@pytest.mark.usefixtures(*fixtures)
async def test_my_endpoint():
    # Test implementation
    pass
```

## Database Test Template

File: `backend/tests/examples/templates/database_test_template.py`

Usage:
```python
from tests.examples.templates.database_test_template import DBTestConfig, get_database_fixtures

config = DBTestConfig(async_mode=False)
fixtures = get_database_fixtures(config)

@pytest.mark.usefixtures(*fixtures)
def test_database_operation():
    # Test implementation
    pass
```

## Integration Test Template

File: `backend/tests/examples/templates/integration_test_template.py`

Usage:
```python
from tests.examples.templates.integration_test_template import IntegrationTestConfig, get_integration_fixtures

config = IntegrationTestConfig(async_mode=True, use_db=True, mock_http=True)
fixtures = get_integration_fixtures(config)

@pytest.mark.usefixtures(*fixtures)
async def test_full_workflow():
    # Test implementation
    pass
``` 