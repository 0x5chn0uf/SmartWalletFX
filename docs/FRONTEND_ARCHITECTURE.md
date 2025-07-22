# Frontend Architecture Guide

> **Audience**: Frontend developers, Claude Code, and contributors working on the React application
> **Focus**: React-specific architecture patterns, best practices, and implementation guidelines

---

## Overview

This document provides detailed architectural guidance for the React frontend of the SmartWalletFX trading bot application. It complements the main [ARCHITECTURE.md](./ARCHITECTURE.md) with frontend-specific patterns and best practices.

### Technology Stack

- **React 19** with **TypeScript** for type-safe component development
- **Vite** for fast development and optimized production builds
- **Redux Toolkit** + **React Query** for hybrid state management
- **Material-UI (MUI)** for consistent design system implementation
- **React Router** for client-side routing and navigation
- **Vitest** + **Cypress** for comprehensive testing strategy
- **MSW** for API mocking during development and testing

---

## 1. Application Architecture Patterns

### Component Architecture Philosophy

The frontend follows a **layered component architecture** with clear separation of concerns:

```
┌─────────────────┐
│     Pages       │ ← Route-level components, data orchestration
├─────────────────┤
│   Features      │ ← Business logic components, domain-specific
├─────────────────┤
│   Components    │ ← Reusable UI components, pure presentation
├─────────────────┤
│ Design System   │ ← Base components, Material-UI wrappers
└─────────────────┘
```

### State Management Strategy

**Hybrid approach** combining Redux Toolkit and React Query:

- **Redux Toolkit**: Application state (auth, UI preferences, cross-cutting concerns)
- **React Query**: Server state (API data, caching, background updates)
- **Component State**: Local UI state (form inputs, toggles, temporary state)

```typescript
// Redux for application state
const authSlice = createSlice({
  name: "auth",
  initialState: { user: null, isAuthenticated: false },
  reducers: {
    /* ... */
  },
});

// React Query for server state
const useWallets = () =>
  useQuery({
    queryKey: ["wallets"],
    queryFn: fetchWallets,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

// Component state for UI
const [isOpen, setIsOpen] = useState(false);
```

---

## 2. Directory Structure & Organization

### Project Structure

```
frontend/src/
├── components/           # Reusable UI components
│   ├── auth/            # Authentication-specific components
│   ├── design-system/   # Base design system components
│   └── Charts/          # Chart and visualization components
├── pages/               # Route-level page components
├── hooks/               # Custom React hooks
├── services/            # API services and external integrations
├── store/               # Redux store configuration and slices
├── types/               # TypeScript type definitions
├── utils/               # Utility functions and helpers
├── mocks/               # MSW mock handlers
└── __tests__/           # Test files (co-located with source)
```

### Component Organization Principles

**Domain-Driven Structure**: Components are organized by business domain rather than technical concerns:

```
components/
├── auth/
│   ├── ProtectedRoute.tsx
│   ├── VerificationBanner.tsx
│   └── OAuthButton.tsx
├── home/
│   ├── HeroSection.tsx
│   ├── FeaturedStats.tsx
│   └── index.ts
└── design-system/
    ├── Button/
    ├── Card/
    └── Form/
```

---

## 3. Component Development Patterns

### Component Classification

**Four types of components** with specific responsibilities:

1. **Pages**: Route-level orchestration, data fetching coordination
2. **Features**: Business logic, domain-specific functionality
3. **Components**: Reusable UI, presentation-focused
4. **Design System**: Base components, Material-UI customizations

### Component Interface Design

**Consistent prop patterns** across all components:

```typescript
interface ComponentProps {
  // Required props first
  data: WalletData;
  onAction: (id: string) => void;

  // Optional props with defaults
  variant?: "primary" | "secondary";
  size?: "small" | "medium" | "large";
  disabled?: boolean;

  // Style and behavior overrides
  sx?: SxProps;
  className?: string;
  "data-testid"?: string;
}

const Component: React.FC<ComponentProps> = ({
  data,
  onAction,
  variant = "primary",
  size = "medium",
  disabled = false,
  sx,
  className,
  "data-testid": testId,
}) => {
  // Implementation
};
```

### Custom Hooks Pattern

**Extract reusable logic** into custom hooks for better testability and reuse:

```typescript
// Custom hook for wallet data management
export const useWalletData = (walletId: string) => {
  const {
    data: wallet,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["wallet", walletId],
    queryFn: () => fetchWalletDetails(walletId),
  });

  const updateWallet = useMutation({
    mutationFn: updateWalletDetails,
    onSuccess: () => {
      queryClient.invalidateQueries(["wallet", walletId]);
    },
  });

  return {
    wallet,
    isLoading,
    error,
    updateWallet: updateWallet.mutate,
    isUpdating: updateWallet.isLoading,
  };
};
```

---

## 4. State Management Architecture

### Redux Store Structure

**Normalized state** with clear domain boundaries:

```typescript
interface RootState {
  auth: AuthState;
  ui: UIState;
  notifications: NotificationState;
  // Server state managed by React Query
}

// Example slice structure
const authSlice = createSlice({
  name: "auth",
  initialState: {
    user: null,
    token: null,
    isAuthenticated: false,
    loginAttempts: 0,
  },
  reducers: {
    loginSuccess: (state, action) => {
      state.user = action.payload.user;
      state.token = action.payload.token;
      state.isAuthenticated = true;
      state.loginAttempts = 0;
    },
    logout: (state) => {
      state.user = null;
      state.token = null;
      state.isAuthenticated = false;
    },
  },
});
```

### React Query Configuration

**Centralized query configuration** with sensible defaults:

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: (failureCount, error) => {
        if (error.status === 401) return false;
        return failureCount < 3;
      },
    },
    mutations: {
      retry: 1,
    },
  },
});
```

---

## 5. Routing & Navigation Architecture

### Route Configuration

**Lazy-loaded routes** with proper error boundaries:

```typescript
// Lazy load page components
const DashboardPage = lazy(() => import('../pages/DashboardPage'));
const WalletDetailPage = lazy(() => import('../pages/WalletDetailPage'));

// Route configuration with protection
const AppRoutes = () => (
  <Routes>
    <Route path="/" element={<LandingPage />} />
    <Route path="/login" element={<LoginRegisterPage />} />

    {/* Protected routes */}
    <Route element={<ProtectedRoute />}>
      <Route
        path="/dashboard"
        element={
          <Suspense fallback={<PageSkeleton />}>
            <DashboardPage />
          </Suspense>
        }
      />
    </Route>

    {/* Catch-all route */}
    <Route path="*" element={<NotFoundPage />} />
  </Routes>
);
```

### Navigation Patterns

**Consistent navigation** with proper state management:

```typescript
const useNavigation = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const navigateWithState = useCallback(
    (to: string, state?: any) => {
      navigate(to, {
        state: { from: location.pathname, ...state },
      });
    },
    [navigate, location.pathname],
  );

  return { navigateWithState, currentPath: location.pathname };
};
```

---

## 6. Material-UI Integration Patterns

### Theme Configuration

**Centralized theming** with design token integration:

```typescript
const theme = createTheme({
  palette: {
    primary: {
      main: "#1976d2",
      light: "#42a5f5",
      dark: "#1565c0",
    },
    background: {
      default: "#f5f5f5",
      paper: "#ffffff",
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: "2.5rem",
      fontWeight: 300,
    },
  },
  spacing: 8, // 8px base unit
});
```

### Component Customization

**Consistent component styling** with sx prop and styled components:

```typescript
// Using sx prop for dynamic styling
<Card
  sx={{
    p: 2,
    mb: 2,
    '&:hover': {
      boxShadow: theme.shadows[4],
    },
  }}
>

// Using styled components for reusable styles
const StyledCard = styled(Card)(({ theme }) => ({
  padding: theme.spacing(2),
  marginBottom: theme.spacing(2),
  '&:hover': {
    boxShadow: theme.shadows[4],
  },
}));
```

---

## 7. API Integration Architecture

### Service Layer Pattern

**Centralized API management** with consistent error handling:

```typescript
// Base API client configuration
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor for authentication
apiClient.interceptors.request.use((config) => {
  const token = store.getState().auth.token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      store.dispatch(logout());
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);
```

### API Service Organization

**Domain-specific service modules** with TypeScript interfaces:

```typescript
// services/wallets.ts
export interface WalletService {
  getWallets(): Promise<Wallet[]>;
  getWalletDetails(id: string): Promise<WalletDetails>;
  updateWallet(id: string, data: UpdateWalletRequest): Promise<Wallet>;
}

export const walletService: WalletService = {
  async getWallets() {
    const response = await apiClient.get<ApiResponse<Wallet[]>>("/wallets");
    return response.data.data;
  },

  async getWalletDetails(id: string) {
    const response = await apiClient.get<ApiResponse<WalletDetails>>(
      `/wallets/${id}`,
    );
    return response.data.data;
  },

  async updateWallet(id: string, data: UpdateWalletRequest) {
    const response = await apiClient.put<ApiResponse<Wallet>>(
      `/wallets/${id}`,
      data,
    );
    return response.data.data;
  },
};
```

---

## 8. Performance Optimization Patterns

### Code Splitting Strategy

**Route-based and component-based** code splitting:

```typescript
// Route-based splitting (already shown above)
const DashboardPage = lazy(() => import('../pages/DashboardPage'));

// Component-based splitting for heavy components
const ChartComponent = lazy(() => import('../components/Charts/TimelineChart'));

// Preload critical routes
const preloadRoute = (routeComponent: () => Promise<any>) => {
  routeComponent();
};

// Preload on user interaction
<Link
  to="/dashboard"
  onMouseEnter={() => preloadRoute(() => import('../pages/DashboardPage'))}
>
  Dashboard
</Link>
```

### Memoization Patterns

**Strategic memoization** for expensive operations:

```typescript
// Memoize expensive calculations
const ExpensiveComponent = React.memo(({ data, filters }) => {
  const processedData = useMemo(() => {
    return data.filter(filters).map(complexTransformation);
  }, [data, filters]);

  const handleClick = useCallback((id: string) => {
    // Event handler
  }, []);

  return <div>{/* Component JSX */}</div>;
});

// Only re-render when specific props change
const areEqual = (prevProps, nextProps) => {
  return (
    prevProps.data.length === nextProps.data.length &&
    prevProps.selectedId === nextProps.selectedId
  );
};

export default React.memo(ExpensiveComponent, areEqual);
```

### Bundle Optimization

**Webpack/Vite configuration** for optimal bundles:

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom"],
          mui: ["@mui/material", "@mui/icons-material"],
          charts: ["recharts"],
        },
      },
    },
  },
  optimizeDeps: {
    include: ["react", "react-dom", "@mui/material"],
  },
});
```

---

## 9. Testing Architecture

### Testing Strategy Overview

**Three-layer testing approach** aligned with the testing pyramid:

1. **Unit Tests** (70%): Components, hooks, utilities
2. **Integration Tests** (20%): API integration, user workflows
3. **E2E Tests** (10%): Critical user paths

### Component Testing Patterns

**React Testing Library** with custom render utilities:

```typescript
// test/utils.tsx
const customRender = (
  ui: ReactElement,
  {
    preloadedState = {},
    store = setupStore(preloadedState),
    ...renderOptions
  } = {}
) => {
  const Wrapper = ({ children }) => (
    <Provider store={store}>
      <ThemeProvider theme={theme}>
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </ThemeProvider>
    </Provider>
  );

  return render(ui, { wrapper: Wrapper, ...renderOptions });
};

// Component test example
describe('WalletCard', () => {
  it('displays wallet information correctly', () => {
    const mockWallet = { id: '1', name: 'Test Wallet', balance: 1000 };

    customRender(<WalletCard wallet={mockWallet} />);

    expect(screen.getByText('Test Wallet')).toBeInTheDocument();
    expect(screen.getByText('$1,000')).toBeInTheDocument();
  });
});
```

### API Testing with MSW

**Mock Service Worker** for realistic API testing:

```typescript
// mocks/handlers.ts
export const handlers = [
  rest.get('/api/wallets', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        data: [
          { id: '1', name: 'Test Wallet', balance: 1000 },
        ],
      })
    );
  }),
];

// Integration test
describe('Wallet Integration', () => {
  it('loads and displays wallets', async () => {
    customRender(<WalletList />);

    await waitFor(() => {
      expect(screen.getByText('Test Wallet')).toBeInTheDocument();
    });
  });
});
```

---

## 10. Security Considerations

### Authentication Flow

**Secure authentication** with proper token management:

```typescript
// Secure token storage (localStorage with evidence)
const authService = {
  setSession(token: string, user: User) {
    localStorage.setItem("token", token);
    localStorage.setItem("user", JSON.stringify(user));
    localStorage.setItem("sessionEvidence", Date.now().toString());
  },

  getSession() {
    const token = localStorage.getItem("token");
    const evidence = localStorage.getItem("sessionEvidence");

    // Validate session evidence (prevent XSS token theft)
    if (
      !token ||
      !evidence ||
      Date.now() - parseInt(evidence) > SESSION_TIMEOUT
    ) {
      this.clearSession();
      return null;
    }

    return { token, user: JSON.parse(localStorage.getItem("user") || "{}") };
  },

  clearSession() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    localStorage.removeItem("sessionEvidence");
  },
};
```

### Input Sanitization

**XSS protection** with proper input handling:

```typescript
import DOMPurify from 'dompurify';

// Sanitize HTML content
const SafeContent = ({ htmlContent }: { htmlContent: string }) => {
  const sanitizedContent = DOMPurify.sanitize(htmlContent);
  return <div dangerouslySetInnerHTML={{ __html: sanitizedContent }} />;
};

// Form validation with security considerations
const validateInput = (value: string, type: 'email' | 'text' | 'number') => {
  const patterns = {
    email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    text: /^[a-zA-Z0-9\s\-_.]+$/, // Allow safe characters only
    number: /^\d+(\.\d+)?$/,
  };

  return patterns[type].test(value);
};
```

---

## 11. Development Workflow Integration

### Development Commands

**Streamlined development** with proper environment setup:

```bash
# Development workflow
npm run dev          # Start development server
npm run test         # Run unit tests in watch mode
npm run test:e2e     # Run Cypress E2E tests
npm run build        # Production build
npm run preview      # Preview production build

# Code quality
npm run lint         # ESLint checking
npm run format       # Prettier formatting
npm run type-check   # TypeScript checking
```

### Environment Configuration

**Environment-specific settings** with validation:

```typescript
// config/environment.ts
interface EnvironmentConfig {
  API_BASE_URL: string;
  OAUTH_GOOGLE_CLIENT_ID: string;
  OAUTH_GITHUB_CLIENT_ID: string;
  ENVIRONMENT: "development" | "staging" | "production";
}

const getEnvironmentConfig = (): EnvironmentConfig => {
  const config = {
    API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
    OAUTH_GOOGLE_CLIENT_ID: import.meta.env.VITE_OAUTH_GOOGLE_CLIENT_ID,
    OAUTH_GITHUB_CLIENT_ID: import.meta.env.VITE_OAUTH_GITHUB_CLIENT_ID,
    ENVIRONMENT: import.meta.env.VITE_ENVIRONMENT || "development",
  };

  // Validate required environment variables
  const requiredVars = ["API_BASE_URL", "OAUTH_GOOGLE_CLIENT_ID"];
  for (const varName of requiredVars) {
    if (!config[varName]) {
      throw new Error(`Missing required environment variable: VITE_${varName}`);
    }
  }

  return config as EnvironmentConfig;
};

export const env = getEnvironmentConfig();
```

---

## 12. Migration and Upgrade Strategies

### Component Migration Patterns

**Incremental migration** for large refactoring:

```typescript
// Legacy component wrapper for gradual migration
const withLegacySupport = <P extends object>(
  NewComponent: React.ComponentType<P>,
  LegacyComponent: React.ComponentType<P>
) => {
  return (props: P & { useLegacy?: boolean }) => {
    if (props.useLegacy) {
      return <LegacyComponent {...props} />;
    }
    return <NewComponent {...props} />;
  };
};

// Feature flag integration
const FeatureFlag = ({ feature, children, fallback = null }) => {
  const isEnabled = useFeatureFlag(feature);
  return isEnabled ? children : fallback;
};
```

### Dependency Upgrade Strategy

**Safe dependency upgrades** with proper testing:

```typescript
// Version compatibility checking
const checkCompatibility = () => {
  const reactVersion = React.version;
  const muiVersion = require("@mui/material/package.json").version;

  // Ensure compatibility matrix
  const compatibility = {
    react: { min: "18.0.0", max: "19.x.x" },
    mui: { min: "5.0.0", max: "6.x.x" },
  };

  // Validate versions...
};
```

---

## Best Practices Summary

### Code Organization

- **Domain-driven structure** over technical grouping
- **Co-located tests** with source files
- **Index files** for clean imports
- **Consistent naming** conventions

### Performance

- **Lazy loading** for routes and heavy components
- **Memoization** for expensive calculations
- **Bundle analysis** and optimization
- **Progressive loading** strategies

### Maintainability

- **TypeScript strict mode** for type safety
- **Consistent prop interfaces** across components
- **Custom hooks** for reusable logic
- **Clear separation** of concerns

### Testing

- **Test behavior**, not implementation
- **Mock at the network boundary** with MSW
- **Integration tests** for critical workflows
- **Accessibility testing** with axe-core

---

_Last updated: July 19, 2025_
_Next review: Monthly during active development_
