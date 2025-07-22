# SmartWalletFX – Testing Guide

> **Purpose**: Describe how we test both the FastAPI backend and React frontend.

---

## 1 Testing Philosophy

We ship only when **all tests are green** and lint passes. Tests are organized by scope and follow the testing pyramid:

### 1.1 Backend Testing (FastAPI)

Tests mirror the hexagonal architecture:

| Scope           | Goal                                       | Boundaries                                              |
| --------------- | ------------------------------------------ | ------------------------------------------------------- |
| **Unit**        | Validate isolated business rules & helpers | No I/O – repositories + services mocked via DIContainer |
| **Integration** | Ensure components collaborate correctly    | Postgres + Redis launched in Docker; Web3 calls faked   |
| **Performance** | Detect regressions on hot paths            | Marked `@pytest.mark.performance`, run nightly          |

Coverage gate: **≥ 90 % lines / 80 % branches**.

### 1.2 Frontend Testing (React)

Tests follow the testing pyramid and user-centric approach:

| Scope           | Goal                                    | Tools & Boundaries                                  |
| --------------- | --------------------------------------- | --------------------------------------------------- |
| **Unit**        | Test individual components & utilities  | Vitest + React Testing Library, mocked dependencies |
| **Integration** | Test component interactions & API flows | MSW for API mocking, Redux store integration        |
| **E2E**         | Validate complete user workflows        | Cypress, real browser automation                    |

Coverage gate: **≥ 85 % lines / 75 % branches** (slightly lower due to UI complexity).

---

## 2 Directory Layout

### 2.1 Backend Layout

```
backend/
└── tests/
    ├── unit/           # Fast, pure‑python
    ├── integration/    # Container‑backed
    ├── performance/    # Benchmarks
    └── fixtures/       # Shared pytest fixtures
```

_Fixtures are grouped by concern_ (`auth.py`, `di_container.py`, `web3.py`, …).

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
    │   ├── e2e/               # E2E test helpers
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

## 3 Running the Test Suites

### 3.1 Backend Testing (Primary targets)

| Purpose                                | Command                                                                  |
| -------------------------------------- | ------------------------------------------------------------------------ |
| **Quiet run (Claude, CI diff checks)** | `make test-quiet` _(maps to_ `pytest -q --tb=short --color=no tests/`_)_ |
| **Full suite**                         | `make test`                                                              |
| **With coverage**                      | `make test-cov`                                                          |
| **Performance only**                   | `make test-perf`                                                         |
| **Single dir**                         | `pytest tests/unit/`                                                     |
| **Single test**                        | `pytest -k "test_name"`                                                  |

### 3.2 Frontend Testing Commands

| Purpose                     | Command                                            | Description                  |
| --------------------------- | -------------------------------------------------- | ---------------------------- |
| **Run all unit tests**      | `npm test`                                         | Vitest in watch mode         |
| **Run tests once**          | `npm run test -- run`                              | Single test run, no watch    |
| **Coverage report**         | `npm run test:coverage`                            | Generate coverage with v8    |
| **Test UI (browser)**       | `npm run test:ui`                                  | Vitest UI in browser         |
| **E2E tests (headless)**    | `npm run cypress:run`                              | Run Cypress tests in CI mode |
| **E2E tests (interactive)** | `npm run cypress:open`                             | Open Cypress test runner     |
| **Specific test file**      | `npm test -- components/Button`                    | Run specific test pattern    |
| **Watch single test**       | `npm test -- --reporter=verbose components/Button` | Verbose single test          |

### 3.3 Useful Frontend Test Options

```bash
# Vitest options
npm test -- --reporter=verbose     # Detailed output
npm test -- --run                  # No watch mode
npm test -- --coverage             # With coverage
npm test -- --ui                   # Browser UI
npm test -- components/            # Test pattern matching

# Cypress options
npx cypress run --spec "cypress/e2e/auth.cy.ts"    # Single spec
npx cypress run --browser chrome                    # Specific browser
npx cypress open --component                        # Component testing mode
```

---

## 4 Frontend Testing Strategies

### 4.1 Unit Testing with Vitest & React Testing Library

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

### 4.2 Component Testing Patterns

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

### 4.3 Integration Testing with MSW

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

### 4.4 Redux Store Testing

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

**Store Integration**: Test components with real store for complex state interactions.

### 4.5 Custom Hook Testing

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

---

## 5 E2E Testing with Cypress

### 5.1 Cypress Configuration

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

### 5.2 E2E Testing Patterns

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

### 5.3 E2E Best Practices

- Use `data-testid` attributes for reliable element selection
- Avoid testing implementation details; focus on user workflows
- Use fixtures for consistent test data
- Clean up data between tests (or use isolated test environments)
- Mock external services that don't need E2E validation

---

## 6 Mock Strategies

### 6.1 MSW (Mock Service Worker)

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

### 6.2 Component Mocking

**Mock Complex Components**:

```typescript
// For tests that don't need chart functionality
vi.mock('../Charts/TimelineChart', () => ({
  default: vi.fn(() => <div data-testid="mocked-chart">Chart</div>)
}));
```

### 6.3 Service Mocking

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

## 7 Backend Testing (Legacy Content)

### 7.1 Fixtures & Dependency Injection

- **DI‑aware**: Tests obtain collaborators via `di_container` fixture to avoid real singletons.
- **Async**: Most fixtures are `async def`; pytest‑asyncio configured in `conftest.py`.
- **Database**: A fresh Postgres container is started per integration session; rolled back between tests.
- **Redis**: Ephemeral container using unique DB index per worker.
- **Web3**: `FakeWeb3` stub injects canned chain data; no external RPC calls.

Example unit fixture pattern:

```python
@pytest.fixture
def wallet_usecase(mock_wallet_repo, mock_user_repo, mock_config, mock_audit):
    return WalletUsecase(mock_wallet_repo, mock_user_repo, mock_config, mock_audit)
```

### 7.2 Markers & Selectors

| Marker                     | Meaning                                        |
| -------------------------- | ---------------------------------------------- |
| `@pytest.mark.integration` | Requires Postgres/Redis containers             |
| `@pytest.mark.performance` | Benchmarks > 500 ms, excluded from default run |
| `@pytest.mark.web3`        | Tests touching blockchain logic                |

Add new markers in `pytest.ini`.

---

## 8 Coverage Requirements and Reporting

### 8.1 Backend Coverage

- **Minimum**: 90% line coverage, 80% branch coverage
- **Command**: `make test-cov`
- **Report formats**: Terminal, HTML, XML for CI

### 8.2 Frontend Coverage

- **Minimum**: 85% line coverage, 75% branch coverage
- **Command**: `npm run test:coverage`
- **Report formats**: Terminal, HTML, JSON
- **Exclusions**: Test files, type definitions, build artifacts

### 8.3 Coverage Configuration

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

## 9 Continuous Integration

### 9.1 GitHub Actions Workflow

**Backend CI**:

- GitHub Actions workflow `ci.yml` runs: `make lint`, `make test-quiet`, coverage upload
- Fail‑fast if coverage gate not met
- Docker services spawned via `services:` matrix

**Frontend CI**:

- Lint: `npm run lint`
- Format check: `npm run format:check`
- Tests: `npm run test:coverage`
- E2E: `npm run cypress:run` (with app server)
- Coverage upload to Codecov

### 9.2 CI Test Strategy

- **Unit tests**: Always run, fast feedback
- **Integration tests**: Run on PR and main branch
- **E2E tests**: Run on main branch and before releases
- **Performance tests**: Nightly runs

---

## 10 Development Workflow

### 10.1 TDD Workflow

1. **Red ➜ Green**: Write failing test, implement code, make it pass
2. **Run Locally**:
   - Backend: `make test-quiet` before each commit
   - Frontend: `npm test` (watch mode during development)
3. **Format & lint**:
   - Backend: `make format && make lint`
   - Frontend: `npm run format && npm run lint`
4. **Push / CI**: Rely on GitHub Actions to repeat the suite

### 10.2 Debugging Workflow

**Backend**:

- Re‑run last failures: `pytest --lf -vv`
- Drop into pdb: `pytest tests/… -k name -x --pdb`
- Show locals in tracebacks: `pytest -vv --showlocals`
- Capture logs: `pytest -s` (disable stdout capture)

**Frontend**:

- Vitest UI: `npm run test:ui` for interactive debugging
- Console debugging: Add `console.log` and run `npm test -- --reporter=verbose`
- Browser debugging: Use `screen.debug()` in tests
- Cypress debugging: `cy.debug()` and time-travel debugging

---

## 11 Adding New Tests

### 11.1 Backend Tests

- Place in the same layer directory (`unit/`, `integration/` …)
- Name file `test_<subject>.py`; name function `test_<expected_behavior>`
- Prefer _Arrange‑Act‑Assert_ structure
- Use `freezegun` for time travel, `pytest-mock` for patches

### 11.2 Frontend Tests

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

**Best Practices**:

- Start with what the user sees and does
- Mock at the boundaries (API calls, complex components)
- Test error states and loading states
- Use semantic HTML and ARIA labels for better tests

---

## 12 Testing Cheat Sheet

### 12.1 Backend Commands

| Need to…                    | Command                                      |
| --------------------------- | -------------------------------------------- |
| Re‑run just‑failed tests    | `pytest --lf`                                |
| Run with coverage report    | `pytest --cov=app --cov-report=term-missing` |
| Show 10 slowest tests       | `pytest --durations=10`                      |
| Generate JUnit XML for IDEs | `pytest --junitxml=report.xml`               |

### 12.2 Frontend Commands

| Need to…                   | Command                   |
| -------------------------- | ------------------------- |
| Run single test file       | `npm test -- Button.test` |
| Run tests with coverage    | `npm run test:coverage`   |
| Debug failing test         | `npm run test:ui`         |
| Run E2E tests headless     | `npm run cypress:run`     |
| Open Cypress interactively | `npm run cypress:open`    |
| Check test file patterns   | `npm test -- --list`      |

### 12.3 Common Patterns

**Frontend Testing Library Queries** (in order of preference):

1. `getByRole` - Semantic HTML roles
2. `getByLabelText` - Form elements
3. `getByText` - Visible text content
4. `getByTestId` - Last resort with `data-testid`

**MSW Request Matching**:

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

_Last updated: 19 July 2025_
