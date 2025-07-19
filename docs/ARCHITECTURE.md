# SmartWalletFX – System Architecture

> **Scope**: This document describes the architecture of SmartWalletFX (React frontend + FastAPI backend).

---

# Backend Architecture

---

## 1 High‑Level Overview

- **Pattern**: Hexagonal (Ports & Adapters) reinforced by explicit **dependency injection**.
- **Language & Runtime**: Python 3.12, fully async.
- **Primary Services**
  - **FastAPI** web layer (HTTP & WebSocket)
  - **PostgreSQL** (async SQLAlchemy 2.0) for persistence
  - **Redis** for caching & Celery message broker
  - **Celery** for background tasks

- **Non‑Backend Components** (out of repo)
  - **React + TradingView** front‑end SPA
  - **Blockchain nodes** (Infura / Alchemy) queried through **Web3.py**

Diagram‑level summary (textual):

```
             ┌────────────┐   Commands / Queries   ┌────────────┐
   HTTP ───▶ │  Endpoints │ ──────────────────────▶│  Usecases  │
             └────────────┘                        └────────────┘
                    ▲                                     │
                    │ DTOs / Schemas                      │ domain ops
                    │                                     ▼
             ┌────────────┐                        ┌────────────┐
             │  Services  │◀── adapters / ports ───│Repositories│
             └────────────┘                        └────────────┘
                    ▲                                     │
                    │ async DB / Redis / Web3             │ SQL / RPC
                    ▼                                     ▼
               External Systems (PostgreSQL, Redis, EVM chains)
```

---

## 2 Layer Breakdown

| Layer            | Package / Path       | Responsibility                                                         |
| ---------------- | -------------------- | ---------------------------------------------------------------------- |
| **Core**         | `app/core/`          | Cross‑cutting infra: config, logging, error handling, database engines |
| **Repositories** | `app/repositories/`  | Data access logic isolated behind interfaces                           |
| **Usecases**     | `app/usecase/`       | Business rules; orchestrate repositories & services                    |
| **Endpoints**    | `app/api/endpoints/` | Transport layer (HTTP/WebSocket) – translate DTO⇄Domain                |
| **Services**     | `app/services/`      | Cross‑cutting helpers (auth, email, OAuth)                             |
| **Tasks**        | `app/tasks/`         | Celery job definitions                                                 |
| **Domain**       | `app/domain/`        | Pydantic models & value objects                                        |

### 2.1 Dependency Injection

`app/di.py` exposes a \`\` that lazily instantiates singletons on first request. All layers request their collaborators through the container; no module‑level globals remain. During testing the container is overridden with fakes/mocks.

### 2.2 Application Factory

`app/main.py` implements `ApplicationFactory`, responsible for:

- creating the FastAPI instance
- wiring middlewares / CORS / exception handlers
- boot‑strapping DIContainer on startup & shutdown hooks

---

## 3 Refactoring Roadmap (Timeline)

| Phase | Status         | Description                                                     |
| ----- | -------------- | --------------------------------------------------------------- |
| 1     | ✅ Done        | Core infra classes converted to DI                              |
| 2     | ✅ Done        | Repositories DI‑enabled                                         |
| 3     | ✅ Done        | Usecases DI‑enabled                                             |
| 4     | ✅ Done        | API endpoints converted to class singletons                     |
| 5     | ✅ Done        | Helper utilities DI‑enabled                                     |
| 6     | 🔄 In progress | **Test suite refactor** – standard fixtures, DI‑aware factories |

---

## 4 Directory Structure (level 2)

```
backend/
├── app/
│   ├── api/endpoints/     # Transport layer
│   ├── core/             # Infrastructure
│   ├── repositories/     # Data mappers
│   ├── services/         # Cross‑cutting
│   ├── usecase/          # Business logic
│   ├── utils/            # Helpers
│   ├── domain/           # Schemas & value objects
│   ├── tasks/            # Celery jobs
│   ├── validators/       # Input validation rules
│   ├── di.py            # DI container
│   └── main.py          # App factory
├── tests/               # Unit, integration, perf
├── migrations/          # Alembic scripts
├── Makefile            # Dev commands
└── pyproject.toml      # Tooling & deps
```

---

## 5 Key Technology Decisions

| Concern             | Choice & Rationale                                                           |
| ------------------- | ---------------------------------------------------------------------------- |
| **Web framework**   | FastAPI + ASGI – best async performance, OpenAPI out of the box              |
| **ORM**             | SQLAlchemy 2.0 async – maturity + type hints                                 |
| **Background jobs** | Celery 5 + Redis – simple, reliable, monitored via Flower                    |
| **Security**        | JWT (RS256) with key rotation; RBAC enforced in endpoints                    |
| **DI**              | Home‑grown container – avoids external runtime deps & keeps startup explicit |

---

## 6 Performance Notes

- Endpoints are fully async; IO‑bound latency hidden behind `await`.
- Connection pools tuned (PostgreSQL: 5↔30, Redis: 10).
- Hot‑path queries cached for 60 s in Redis.
- Prometheus metrics scraped every 15 s; Grafana dashboard available.

---

## 7 Security Posture

- Static analysis: **ruff**, **bandit**, **safety** in CI.
- Strict CORS & rate limiting on auth routes.
- Bcrypt‑hashed passwords; env‑rotated secrets.
- SQL injection mitigated via SQLAlchemy Core & Pydantic validation.

---

## 8 Testing Strategy (Backend)

- **Unit**: repo & usecase isolation via DI mocks.
- **Integration**: spin‑up PostgreSQL + Redis containers (docker‑compose) per job.
- **Performance**: `-m performance` markers; run nightly.
- **Coverage gate**: 90 % lines / 80 % branches.

---

## 9 How to Extend (Backend)

1. Add new repository class under `app/repositories/…`.
2. Register it inside `DIContainer.register()`.
3. Inject into a usecase via constructor.
4. Expose via endpoint method.

No global state; unit tests mock at any seam.

---

# Frontend Architecture

> **Scope**: This section describes the React frontend architecture (TypeScript + modern React ecosystem).

---

## 10 Frontend High‑Level Overview

- **Pattern**: Component‑based architecture with centralized state management
- **Language & Runtime**: TypeScript 4.9, React 19, Node.js
- **Primary Technologies**
  - **React 19** with functional components & hooks
  - **Vite** for build system & development server
  - **Redux Toolkit** for complex state management
  - **React Query (TanStack)** for server state & caching
  - **Material‑UI (MUI)** for design system & components
  - **React Router** for client‑side routing

- **Build & Testing Stack**
  - **Vitest** for unit testing with coverage
  - **Cypress** for end‑to‑end testing
  - **MSW (Mock Service Worker)** for API mocking
  - **ESLint + Prettier** for code quality

Architectural overview:

```
    ┌─────────────┐   HTTP requests   ┌─────────────┐
    │  React App  │ ─────────────────▶│   FastAPI   │
    └─────────────┘                   │   Backend   │
           │                          └─────────────┘
           ▼
    ┌─────────────┐
    │   Routing   │   React Router
    │ (react-router) │
    └─────────────┘
           │
           ▼
    ┌─────────────┐   Pages render   ┌─────────────┐
    │    Pages    │ ◀───────────────▶│ Components  │
    └─────────────┘                  └─────────────┘
           │                                │
           ▼                                ▼
    ┌─────────────┐   State flows    ┌─────────────┐
    │Redux Store  │ ◀───────────────▶│    Hooks    │
    │+ React Query│                  │  (custom)   │
    └─────────────┘                  └─────────────┘
           │
           ▼
    ┌─────────────┐
    │   Services  │   API calls via axios
    │  (api.ts)   │
    └─────────────┘
```

---

## 11 Frontend Layer Breakdown

| Layer             | Location          | Responsibility                                                |
| ----------------- | ----------------- | ------------------------------------------------------------- |
| **Pages**         | `src/pages/`      | Top‑level route components; coordinate data fetching & layout |
| **Components**    | `src/components/` | Reusable UI components; organized by feature/domain           |
| **State (Redux)** | `src/store/`      | Application state slices for complex state management         |
| **State (Query)** | React Query hooks | Server state caching, synchronization, and mutation           |
| **Services**      | `src/services/`   | API communication layer with axios interceptors               |
| **Hooks**         | `src/hooks/`      | Custom React hooks for shared logic                           |
| **Types**         | `src/types/`      | TypeScript interfaces and type definitions                    |
| **Utils**         | `src/utils/`      | Pure utility functions and data transformers                  |
| **Theme**         | `src/theme/`      | Design tokens and Material‑UI theme configuration             |
| **Tests**         | `src/__tests__/`  | Unit tests mirroring the source structure                     |

### 11.1 State Management Strategy

**Dual State Architecture:**

1. **Redux Toolkit** for client‑side application state:
   - Authentication status and user profile
   - UI state (notifications, modals, forms)
   - Application settings and preferences

2. **React Query (TanStack Query)** for server state:
   - API data caching and synchronization
   - Background refetching and invalidation
   - Optimistic updates and mutation handling

**Benefits:**

- Clear separation of concerns
- Automatic cache invalidation
- Reduced boilerplate for API operations
- Better performance through intelligent caching

### 11.2 Component Architecture

**Material‑UI Integration:**

- Consistent design system via MUI components
- Custom theme with design tokens (`src/theme/generated.ts`)
- Responsive breakpoints and spacing system
- Dark mode support through theme configuration

**Component Organization:**

```
src/components/
├── auth/              # Authentication components
├── design-system/     # Base design components
├── home/              # Landing page components
├── Charts/           # Data visualization components
└── [feature]/        # Feature‑specific components
```

**Component Patterns:**

- Functional components with TypeScript
- Props interfaces for type safety
- Custom hooks for component logic
- Material‑UI styling with theme integration

---

## 12 Frontend Directory Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── auth/           # Authentication components
│   │   ├── Charts/         # Data visualization
│   │   ├── design-system/  # Base design components
│   │   └── home/           # Landing page components
│   ├── pages/              # Route‑level page components
│   ├── store/              # Redux slices and store config
│   ├── services/           # API client and service functions
│   ├── hooks/              # Custom React hooks
│   ├── types/              # TypeScript type definitions
│   ├── utils/              # Pure utility functions
│   ├── theme/              # Design tokens and MUI theme
│   ├── mocks/              # MSW request handlers
│   ├── providers/          # Context providers
│   └── __tests__/          # Unit and integration tests
├── cypress/                # E2E test specifications
├── public/                 # Static assets
├── dist/                   # Production build output
├── package.json            # Dependencies and scripts
├── tsconfig.json           # TypeScript configuration
├── vite.config.mts         # Vite build configuration
└── cypress.config.ts       # Cypress test configuration
```

---

## 13 Build System & Asset Management

**Vite Configuration:**

- Lightning‑fast development server with HMR
- TypeScript compilation with type checking
- CSS preprocessing and optimization
- Asset bundling and tree‑shaking for production

**Development Workflow:**

```bash
npm run dev          # Start development server
npm run build        # Production build
npm run test         # Run unit tests with Vitest
npm run test:coverage # Generate coverage reports
npm run cypress:open # Open Cypress test runner
```

**Performance Optimizations:**

- Code splitting at route level
- Lazy loading for non‑critical components
- Asset optimization and compression
- Bundle analysis and tree‑shaking

---

## 14 Frontend‑Backend Integration

**API Communication:**

- Centralized Axios client (`src/services/api.ts`)
- Automatic token management and refresh
- Request/response interceptors for error handling
- Environment‑based API URL configuration

**Authentication Flow:**

1. JWT token storage in localStorage
2. Automatic token injection via Axios interceptors
3. Silent refresh mechanism for expired tokens
4. Session state management through Redux

**Data Flow Patterns:**

```
User Action → Component → Redux Action/React Query → API Service → Backend
                  ↓                                      ↓
            State Update ←─────── Response Processing ←───┘
                  ↓
            Component Re‑render
```

**Error Handling:**

- Global error boundary for uncaught errors
- API error interceptors with retry logic
- User‑friendly error notifications
- Fallback UI states for failed requests

---

## 15 TypeScript Implementation

**Type Safety Strategy:**

- Strict TypeScript configuration
- Interface definitions for all API responses
- Props typing for all React components
- Custom type guards for runtime validation

**Key Type Categories:**

```typescript
// API Response Types
interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

// Domain Types
interface UserProfile {
  id: string;
  username: string;
  email: string;
  email_verified: boolean;
}

// State Types
interface AuthState {
  isAuthenticated: boolean;
  user: UserProfile | null;
  status: "idle" | "loading" | "succeeded" | "failed";
}
```

**Benefits:**

- Compile‑time error detection
- Enhanced IDE support and autocomplete
- Self‑documenting code through interfaces
- Refactoring safety across the codebase

---

## 16 Testing Strategy (Frontend)

**Testing Pyramid:**

1. **Unit Tests (Vitest):**
   - Component rendering and behavior
   - Custom hooks logic
   - Utility function validation
   - Redux slice logic

2. **Integration Tests:**
   - API service integration
   - Component interaction flows
   - State management integration

3. **E2E Tests (Cypress):**
   - User workflow validation
   - Cross‑browser compatibility
   - Visual regression testing

**Mock Strategy:**

- MSW for API mocking in tests
- Component mocks for unit isolation
- Redux store mocking for state tests

**Coverage Requirements:**

- 85% line coverage for components
- 90% coverage for utilities and services
- Critical user flows covered by E2E tests

---

## 17 Design System Integration

**Material‑UI Theme System:**

- Centralized design tokens via Style Dictionary
- Auto‑generated theme configuration
- Consistent spacing, typography, and colors
- Responsive breakpoint system

**Design Token Generation:**

```bash
npm run build:tokens  # Generate theme from style dictionary
```

**Accessibility Standards:**

- WCAG 2.1 AA compliance
- Semantic HTML structure
- Keyboard navigation support
- Screen reader compatibility
- Color contrast validation

---

## 18 Performance & Optimization

**Bundle Optimization:**

- Tree‑shaking for unused code elimination
- Dynamic imports for route‑based code splitting
- Asset optimization and compression
- Cache‑busting for static resources

**Runtime Performance:**

- React.memo for expensive component renders
- useMemo/useCallback for computation optimization
- Virtualization for large data sets
- Image lazy loading and optimization

**Monitoring:**

- Web Vitals measurement
- Bundle analyzer for size monitoring
- Performance profiling in development
- Error tracking and reporting

---

_Last updated: 19 July 2025_
