# SmartWalletFX – Comprehensive Testing Guide

> **Purpose**: Complete guide for testing the FastAPI backend and React frontend with enhanced test infrastructure.

---

## Table of Contents

1. [Testing Philosophy](#1-testing-philosophy)
2. [Test Architecture](#2-test-architecture)
3. [Running Test Suites](#3-running-test-suites)
4. [Backend Testing](#4-backend-testing)
5. [Frontend Testing](#5-frontend-testing)
6. [Enhanced Test Infrastructure](#6-enhanced-test-infrastructure)
7. [Docker Test Infrastructure](#7-docker-test-infrastructure)
8. [Mock Strategies](#8-mock-strategies)
9. [Coverage Requirements](#9-coverage-requirements)
10. [CI/CD Integration](#10-cicd-integration)
11. [Development Workflow](#11-development-workflow)
12. [Best Practices](#12-best-practices)
13. [Migration Guide](#13-migration-guide)
14. [Troubleshooting](#14-troubleshooting)

---

## 1 Testing Philosophy

We ship only when **all tests are green** and lint passes. Tests are organized by scope and follow the testing pyramid:

### 1.1 Backend Testing (FastAPI)

Tests mirror the hexagonal architecture with enhanced infrastructure:

| Scope           | Goal                                       | Boundaries                                              |
| --------------- | ------------------------------------------ | ------------------------------------------------------- |
| **Unit**        | Validate isolated business rules & helpers | No I/O – repositories + services mocked via DIContainer |
| **Integration** | Ensure components collaborate correctly    | Real Postgres + Redis in Docker; Web3 calls mocked     |
| **Performance** | Detect regressions on hot paths            | Marked `@pytest.mark.performance`, run nightly          |

**Key Benefits**:
- ⚡ **52x faster unit tests** with optimized configurations
- 🐳 **Docker-based integration testing** with isolated services
- 🎭 **Sophisticated mocking** with realistic failure scenarios
- 🔧 **Flexible DI container** system for different test types

Coverage gate: **≥ 90% lines / 80% branches**.

### 1.2 Frontend Testing (React)

Tests follow the testing pyramid and user-centric approach:

| Scope           | Goal                                    | Tools & Boundaries                                  |
| --------------- | --------------------------------------- | --------------------------------------------------- |
| **Unit**        | Test individual components & utilities  | Vitest + React Testing Library, mocked dependencies |
| **Integration** | Test component interactions & API flows | MSW for API mocking, Redux store integration        |
| **E2E**         | Validate complete user workflows        | Cypress, real browser automation                    |

Coverage gate: **≥ 85% lines / 75% branches** (slightly lower due to UI complexity).

---

## 2 Test Architecture

### 2.1 Enhanced Backend Layout

```
backend/
└── tests/
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
        │   ├── enhanced_mocks/# Enhanced mock system
        │   ├── test_di_container.py # Test DI container
        │   ├── test_config.py       # Test configurations
        │   └── test_database.py     # Database test utilities
        └── utils/             # Test utilities
```

### 2.2 Frontend Layout

```
frontend/
└── src/
    ├── __tests__/              # Main test directory
    │   ├── components/         # Component unit tests
    │   ├── hooks/             # Custom hook tests
    │   ├── pages/             # Page component tests
    │   ├── services/          # API service tests
    │   ├── store/             # Redux slice tests
    │   ├── utils/             # Utility function tests
    │   ├── integration/       # Integration tests
    │   └── unit/              # Additional unit tests
    ├── mocks/                 # MSW mock handlers
    │   ├── handlers.ts        # API mock handlers
    │   ├── browser.ts         # Browser MSW setup
    │   └── server.ts          # Node MSW setup
    ├── test/
    │   └── setup.ts           # Vitest global setup
    └── tests/                 # Legacy test location
└── cypress/
    ├── e2e/                   # Cypress E2E tests
    ├── fixtures/              # Test data fixtures
    └── support/               # Cypress commands & utilities
```

---

## 3 Running Test Suites

### 3.1 Backend Testing Commands

| Purpose                                | Command                                                                  |
| -------------------------------------- | ------------------------------------------------------------------------ |
| **Quiet run (Claude, CI diff checks)** | `make test-quiet` _(maps to_ `pytest -q --tb=short --color=no tests/`_)_ |
| **Full suite**                         | `make test`                                                              |
| **With coverage**                      | `make test-cov`                                                          |
| **Performance only**                   | `make test-perf`                                                         |
| **Integration tests with Docker**      | `make test-integration-docker`                                           |
| **Unit tests only**                    | `make test-unit`                                                         |
| **Single dir**                         | `pytest tests/unit/`                                                     |
| **Single test**                        | `pytest -k "test_name"`                                                  |

### 3.2 Frontend Testing Commands

| Purpose                     | Command                                            | Description                  |
| --------------------------- | -------------------------------------------------- | ---------------------------- |
| **Run all unit tests**      | `npm test`                                         | Vitest in watch mode         |
| **Run tests once**          | `npm run test -- --run`                            | Single test run, no watch    |
| **Coverage report**         | `npm run test:coverage`                            | Generate coverage with v8    |
| **Test UI (browser)**       | `npm run test:ui`                                  | Vitest UI in browser         |
| **E2E tests (headless)**    | `npm run cypress:run`                              | Run Cypress tests in CI mode |
| **E2E tests (interactive)** | `npm run cypress:open`                             | Open Cypress test runner     |
| **Specific test file**      | `npm test -- components/Button`                    | Run specific test pattern    |
| **Watch single test**       | `npm test -- --reporter=verbose components/Button` | Verbose single test          |

### 3.3 Docker Test Infrastructure Commands

```bash
# Start test infrastructure
make test-docker-up

# Run integration tests with Docker
make test-integration-docker

# Run all test scenarios
make test-all-scenarios

# Clean up test infrastructure
make test-docker-clean
```

---

## 4 Backend Testing

### 4.1 Unit Tests with Enhanced Mocks

Fast, isolated tests that use sophisticated mocking for external dependencies:

```python
# tests/domains/auth/unit/test_auth_service.py
import pytest
from unittest.mock import AsyncMock

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

### 4.2 Integration Tests with Real Database

Tests that use real database connections and verify actual data persistence:

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

### 4.3 Enhanced Mock System

The enhanced mock system provides realistic behaviors and comprehensive tracking:

#### Basic Mock Usage

```python
from tests.shared.fixtures.enhanced_mocks import (
    MockBehavior,
    MockServiceFactory,
)
from tests.shared.fixtures.enhanced_mocks.assertions import MockAssertions

# Create mocks with specific behaviors
user_repo = MockServiceFactory.create_user_repository(MockBehavior.SUCCESS)
email_service = MockServiceFactory.create_email_service(MockBehavior.SLOW_RESPONSE)
failing_service = MockServiceFactory.create_file_upload_service(MockBehavior.FAILURE)
```

#### Mock Behaviors

```python
class MockBehavior(Enum):
    SUCCESS = "success"          # Normal operation
    FAILURE = "failure"          # Service failures
    TIMEOUT = "timeout"          # Network timeouts
    RATE_LIMITED = "rate_limited"    # Rate limiting
    SLOW_RESPONSE = "slow_response"  # Performance issues
```

#### Stateful Mocks

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

#### Failure Scenario Testing

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

### 4.4 Fixtures & Dependency Injection

- **DI-aware**: Tests obtain collaborators via `di_container` fixture to avoid real singletons
- **Async**: Most fixtures are `async def`; pytest-asyncio configured in `conftest.py`
- **Database**: A fresh Postgres container is started per integration session; rolled back between tests
- **Redis**: Ephemeral container using unique DB index per worker
- **Web3**: `FakeWeb3` stub injects canned chain data; no external RPC calls

Example unit fixture pattern:

```python
@pytest.fixture
def wallet_usecase(mock_wallet_repo, mock_user_repo, mock_config, mock_audit):
    return WalletUsecase(mock_wallet_repo, mock_user_repo, mock_config, mock_audit)
```

### 4.5 Test Markers & Selectors

| Marker                     | Meaning                                        |
| -------------------------- | ---------------------------------------------- |
| `@pytest.mark.integration` | Requires Postgres/Redis containers             |
| `@pytest.mark.performance` | Benchmarks > 500 ms, excluded from default run |
| `@pytest.mark.web3`        | Tests touching blockchain logic                |

Add new markers in `pytest.ini`.

---

## 5 Frontend Testing

### 5.1 Unit Testing with Vitest & React Testing Library

**Philosophy**: Test components in isolation with mocked dependencies.

```typescript
// Example: Component unit test
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import { store } from '../../store';
import LoginForm from '../LoginForm';

describe('LoginForm', () => {
  const renderWithProvider = (component: JSX.Element) => {
    return render(
      <Provider store={store}>
        {component}
      </Provider>
    );
  };

  it('should submit form with valid credentials', async () => {
    const user = userEvent.setup();
    const mockSubmit = vi.fn();

    renderWithProvider(<LoginForm onSubmit={mockSubmit} />);

    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'password123');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    expect(mockSubmit).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password123'
    });
  });
});
```

### 5.2 Component Testing Patterns

**Render Helpers**: Create reusable render functions for common setups:

```typescript
// test-utils.tsx
import { render } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { store } from '../store';
import { theme } from '../theme';

export const renderWithProviders = (ui: JSX.Element) => {
  return render(
    <Provider store={store}>
      <BrowserRouter>
        <ThemeProvider theme={theme}>
          {ui}
        </ThemeProvider>
      </BrowserRouter>
    </Provider>
  );
};
```

**Testing Guidelines**:

- Focus on user interactions and outcomes, not implementation details
- Use semantic queries (`getByRole`, `getByLabelText`) over test IDs when possible
- Test accessibility with `@axe-core/react` for critical components
- Mock external dependencies (APIs, complex children) at the component boundary

### 5.3 Integration Testing with MSW

**API Mocking Strategy**: Use MSW to intercept network requests:

```typescript
// handlers.ts
import { http, HttpResponse } from "msw";

export const handlers = [
  http.get("/api/wallets", () => {
    return HttpResponse.json({
      wallets: [{ id: "1", name: "Main Wallet", balance: 1000 }],
    });
  }),

  http.post("/api/auth/login", async ({ request }) => {
    const { email, password } = await request.json();

    if (email === "valid@example.com" && password === "correct") {
      return HttpResponse.json({ token: "mock-jwt", user: { id: 1 } });
    }

    return HttpResponse.json({ error: "Invalid credentials" }, { status: 401 });
  }),
];
```

**Integration Test Example**:

```typescript
// WalletList.integration.test.tsx
import { renderWithProviders } from '../test-utils';
import { waitFor } from '@testing-library/react';
import WalletList from '../WalletList';

describe('WalletList Integration', () => {
  it('should load and display wallets from API', async () => {
    renderWithProviders(<WalletList />);

    await waitFor(() => {
      expect(screen.getByText('Main Wallet')).toBeInTheDocument();
      expect(screen.getByText('$1,000')).toBeInTheDocument();
    });
  });
});
```

### 5.4 Redux Store Testing

**Slice Testing**: Test reducers and actions in isolation:

```typescript
// authSlice.test.ts
import authReducer, { loginAsync, logout } from "../authSlice";

describe("authSlice", () => {
  it("should handle successful login", () => {
    const initialState = { user: null, isAuthenticated: false };
    const action = {
      type: loginAsync.fulfilled.type,
      payload: { user: { id: 1, email: "test@example.com" } },
    };

    const state = authReducer(initialState, action);

    expect(state.isAuthenticated).toBe(true);
    expect(state.user).toEqual({ id: 1, email: "test@example.com" });
  });
});
```

### 5.5 Custom Hook Testing

**Hook Testing Pattern**:

```typescript
// useAuth.test.tsx
import { renderHook, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { store } from '../../store';
import { useAuth } from '../useAuth';

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <Provider store={store}>{children}</Provider>
);

describe('useAuth', () => {
  it('should return user when authenticated', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toBeDefined();
    });
  });
});
```

### 5.6 E2E Testing with Cypress

#### Cypress Configuration

Key configuration in `cypress.config.ts`:

```typescript
export default defineConfig({
  e2e: {
    baseUrl: "http://localhost:3000",
    video: false,
    screenshotOnRunFailure: true,
    viewportWidth: 1280,
    viewportHeight: 720,
  },
});
```

#### E2E Testing Patterns

**Page Object Pattern**:

```typescript
// cypress/support/pageObjects/LoginPage.ts
export class LoginPage {
  visit() {
    cy.visit("/login");
  }

  fillEmail(email: string) {
    cy.get('[data-testid="email-input"]').type(email);
  }

  fillPassword(password: string) {
    cy.get('[data-testid="password-input"]').type(password);
  }

  submit() {
    cy.get('[data-testid="login-button"]').click();
  }
}
```

**E2E Test Example**:

```typescript
// cypress/e2e/auth-flow.cy.ts
import { LoginPage } from "../support/pageObjects/LoginPage";

describe("Authentication Flow", () => {
  const loginPage = new LoginPage();

  it("should allow user to login and access dashboard", () => {
    loginPage.visit();
    loginPage.fillEmail("user@example.com");
    loginPage.fillPassword("password123");
    loginPage.submit();

    cy.url().should("include", "/dashboard");
    cy.contains("Welcome to your dashboard").should("be.visible");
  });
});
```

#### E2E Best Practices

- Use `data-testid` attributes for reliable element selection
- Avoid testing implementation details; focus on user workflows
- Use fixtures for consistent test data
- Clean up data between tests (or use isolated test environments)
- Mock external services that don't need E2E validation

---

## 6 Enhanced Test Infrastructure

### 6.1 Test Categories

**Unit Tests**: Fast, isolated tests that use mocks for all external dependencies
**Integration Tests**: Tests that use real database connections and verify actual data persistence
**Performance Tests**: Benchmarking and performance regression testing
**E2E Tests**: Full system testing with external services

### 6.2 Test Data Management

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

### 6.3 Fixture Usage

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

---

## 7 Docker Test Infrastructure

### 7.1 Test Services

The Docker test infrastructure provides isolated services:

```yaml
# docker-compose.test.yml (automatically managed)
services:
  postgres-test: # Port 55432 (isolated from dev)
  redis-test: # Port 6380 (isolated from dev)
  backend-test: # Port 8001 (for integration testing)
```

### 7.2 Configuration

```python
# Integration test configuration
from tests.shared.fixtures.test_config import create_integration_test_config

config = create_integration_test_config(
    test_db_url="postgresql+asyncpg://testuser:testpass@localhost:55432/test_smartwallet"
)
```

### 7.3 Environment Variables

```bash
# Test type selection
export TEST_TYPE=unit|integration|performance

# Database configuration
export TEST_DB_URL="postgresql+asyncpg://testuser:testpass@localhost:55432/test_smartwallet"

# Performance optimization
export BCRYPT_ROUNDS=4

# Docker usage
export USE_DOCKER_TESTS=true
```

---

## 8 Mock Strategies

### 8.1 MSW (Mock Service Worker)

**Setup**: MSW intercepts requests at the network level:

```typescript
// mocks/browser.ts
import { setupWorker } from "msw/browser";
import { handlers } from "./handlers";

export const worker = setupWorker(...handlers);

// mocks/server.ts (for Node.js/testing)
import { setupServer } from "msw/node";
import { handlers } from "./handlers";

export const server = setupServer(...handlers);
```

**Test Setup**:

```typescript
// test/setup.ts
import { beforeAll, afterEach, afterAll } from "vitest";
import { server } from "../mocks/server";

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

### 8.2 Component Mocking

**Mock Complex Components**:

```typescript
// For tests that don't need chart functionality
vi.mock('../Charts/TimelineChart', () => ({
  default: vi.fn(() => <div data-testid="mocked-chart">Chart</div>)
}));
```

### 8.3 Service Mocking

**API Service Mocks**:

```typescript
vi.mock("../services/api", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));
```

---

## 9 Coverage Requirements

### 9.1 Backend Coverage

- **Minimum**: 90% line coverage, 80% branch coverage
- **Command**: `make test-cov`
- **Report formats**: Terminal, HTML, XML for CI

### 9.2 Frontend Coverage

- **Minimum**: 85% line coverage, 75% branch coverage
- **Command**: `npm run test:coverage`
- **Report formats**: Terminal, HTML, JSON
- **Exclusions**: Test files, type definitions, build artifacts

### 9.3 Coverage Configuration

**Frontend (vitest.config.mts)**:

```typescript
coverage: {
  provider: 'v8',
  reporter: ['text', 'json', 'html'],
  exclude: [
    'node_modules/**',
    'src/test/**',
    '**/*.d.ts',
    '**/*.test.{ts,tsx}',
    'dist/**',
  ],
  include: ['src/**/*.{ts,tsx}']
}
```

---

## 10 CI/CD Integration

### 10.1 GitHub Actions Workflow

The enhanced CI/CD pipeline provides:

- **Parallel test execution** across multiple domains
- **Matrix testing** for different test groups
- **Docker integration** for realistic testing
- **Performance benchmarking**
- **Coverage reporting** with Codecov

### 10.2 Pipeline Stages

1. **Security & Quality** (10 min) - Bandit, Safety, Ruff, MyPy
2. **Unit Tests** (15 min) - Parallel execution by domain
3. **Integration Tests** (30 min) - Real database testing
4. **Performance Tests** (20 min) - Benchmarking
5. **Docker Integration** (25 min) - Full system testing

### 10.3 Branch Protection

Configure branch protection with required status checks:

- `Security & Quality Checks`
- `Unit Tests (auth, users, wallets, tokens, email, oauth)`
- `Integration Tests`
- `Docker Integration Test`

### 10.4 CI Test Strategy

- **Unit tests**: Always run, fast feedback
- **Integration tests**: Run on PR and main branch
- **E2E tests**: Run on main branch and before releases
- **Performance tests**: Nightly runs

---

## 11 Development Workflow

### 11.1 TDD Workflow

1. **Red ➜ Green**: Write failing test, implement code, make it pass
2. **Run Locally**:
   - Backend: `make test-quiet` before each commit
   - Frontend: `npm test` (watch mode during development)
3. **Format & lint**:
   - Backend: `make format && make lint`
   - Frontend: `npm run format && npm run lint`
4. **Push / CI**: Rely on GitHub Actions to repeat the suite

### 11.2 Debugging Workflow

**Backend**:

- Re-run last failures: `pytest --lf -vv`
- Drop into pdb: `pytest tests/… -k name -x --pdb`
- Show locals in tracebacks: `pytest -vv --showlocals`
- Capture logs: `pytest -s` (disable stdout capture)

**Frontend**:

- Vitest UI: `npm run test:ui` for interactive debugging
- Console debugging: Add `console.log` and run `npm test -- --reporter=verbose`
- Browser debugging: Use `screen.debug()` in tests
- Cypress debugging: `cy.debug()` and time-travel debugging

### 11.3 IDE Integration

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

---

## 12 Best Practices

### 12.1 Test Organization

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

### 12.2 Mock Configuration

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

### 12.3 Assertion Patterns

```python
# Use enhanced assertions
mock_assertions.assert_called_once_with(
    mock_service, "method_name", expected_arg
)

# Verify state changes
assert len(mock_service.get_calls("create")) == 2
assert mock_service.users["user_id"].email == "new@email.com"
```

### 12.4 Error Testing

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

### 12.5 Test Naming Conventions

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

### 12.6 Frontend Best Practices

**Naming Conventions**:

- Unit tests: `ComponentName.test.tsx`
- Integration tests: `feature.integration.test.tsx`
- E2E tests: `workflow.cy.ts`

**Test Structure**:

```typescript
describe("ComponentName", () => {
  // Arrange
  const defaultProps = {
    /* ... */
  };

  beforeEach(() => {
    // Setup
  });

  it("should behave as expected when condition", () => {
    // Arrange
    // Act
    // Assert
  });
});
```

**Guidelines**:

- Start with what the user sees and does
- Mock at the boundaries (API calls, complex components)
- Test error states and loading states
- Use semantic HTML and ARIA labels for better tests

**Frontend Testing Library Queries** (in order of preference):

1. `getByRole` - Semantic HTML roles
2. `getByLabelText` - Form elements
3. `getByText` - Visible text content
4. `getByTestId` - Last resort with `data-testid`

---

## 13 Migration Guide

### 13.1 From Old Mocks to Enhanced Mocks

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

    result = await service.create_user(user_data)

    # Enhanced assertions with call tracking
    mock_assertions.assert_called_once_with(
        mock_user_repository_enhanced, "get_by_id", user_id
    )

    # Verify state
    assert len(mock_user_repository_enhanced.users) == 1
```

### 13.2 From Basic Tests to Integration Tests

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

### 13.3 Updating CI/CD

1. **Update workflow files** with enhanced pipeline stages
2. **Update branch protection** rules
3. **Configure environment variables**
4. **Set up Codecov integration**

---

## 14 Troubleshooting

### 14.1 Common Issues

1. **Import Errors**: Ensure all fixture imports are correct
2. **Mock Configuration**: Verify mock behaviors are set before test execution
3. **Database Issues**: Check Docker services are running for integration tests
4. **Performance**: Use unit tests for fast feedback, integration for verification

### 14.2 Debug Commands

```bash
# Check Docker test services
docker-compose -f docker-compose.test.yml ps

# Verify test database connection
TEST_DB_URL="postgresql+asyncpg://testuser:testpass@localhost:55432/test_smartwallet" \
python -c "from sqlalchemy import create_engine; print('Connection OK')"

# Run single test with verbose output
pytest tests/path/to/test.py::test_function -v -s --tb=long
```

### 14.3 Backend Commands Cheat Sheet

| Need to…                    | Command                                      |
| --------------------------- | -------------------------------------------- |
| Re-run just-failed tests    | `pytest --lf`                                |
| Run with coverage report    | `pytest --cov=app --cov-report=term-missing` |
| Show 10 slowest tests       | `pytest --durations=10`                      |
| Generate JUnit XML for IDEs | `pytest --junitxml=report.xml`               |

### 14.4 Frontend Commands Cheat Sheet

| Need to…                   | Command                   |
| -------------------------- | ------------------------- |
| Run single test file       | `npm test -- Button.test` |
| Run tests with coverage    | `npm run test:coverage`   |
| Debug failing test         | `npm run test:ui`         |
| Run E2E tests headless     | `npm run cypress:run`     |
| Open Cypress interactively | `npm run cypress:open`    |
| Check test file patterns   | `npm test -- --list`      |

### 14.5 MSW Request Matching

```typescript
// Exact match
http.get("/api/users", handler);

// Path parameters
http.get("/api/users/:id", handler);

// Query parameters (access via request.url)
http.get("/api/search", ({ request }) => {
  const url = new URL(request.url);
  const query = url.searchParams.get("q");
});
```

---

This comprehensive testing infrastructure provides a solid foundation for reliable, fast, and comprehensive testing. Follow these patterns for consistent, maintainable tests that provide confidence in code quality and system reliability.

_Last updated: 26 July 2025_