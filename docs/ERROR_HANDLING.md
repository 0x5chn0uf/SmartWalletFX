# Error Handling Guide

> **Audience**: Claude Code and contributors working with error handling patterns
> **Purpose**: Comprehensive guide to the standardized error handling system used throughout the FastAPI application

## Overview

The trading bot backend implements a centralized error handling system using FastAPI's global exception handlers. This document explains how errors are structured, processed, and returned to clients, with patterns for consistent error handling across endpoints.

## Table of Contents

1. [Standard Error Response Format](#standard-error-response-format)
2. [Error Codes and Status Codes](#error-codes-and-status-codes)
3. [Exception Handling Architecture](#exception-handling-architecture)
4. [Request Tracing](#request-tracing)
5. [Audit Logging](#audit-logging)
6. [Client-Side Error Handling](#client-side-error-handling)
7. [Testing Error Scenarios](#testing-error-scenarios)
8. [Adding Custom Error Types](#adding-custom-error-types)

## Standard Error Response Format

All API errors follow a consistent JSON structure defined by the `ErrorResponse` schema:

```json
{
  "detail": "Human-readable error message",
  "code": "MACHINE_READABLE_CODE",
  "status_code": 401,
  "trace_id": "7f580fb3-4d94-4b95-9d0b-87850c2c7399"
}
```

| Field         | Type          | Description                                                              |
| ------------- | ------------- | ------------------------------------------------------------------------ |
| `detail`      | string        | Human-readable error message suitable for display to end users           |
| `code`        | string        | Machine-readable error code for programmatic handling                    |
| `status_code` | integer       | HTTP status code                                                         |
| `trace_id`    | string (UUID) | Unique identifier for the request, used for correlation with server logs |

This format ensures that:

1. Users receive clear, actionable error messages
2. Clients can programmatically handle different error types
3. Support teams can correlate client errors with server logs

## Error Codes and Status Codes

### Standard Error Codes

| Code               | Description                                      | Typical Status Codes |
| ------------------ | ------------------------------------------------ | -------------------- |
| `AUTH_FAILURE`     | Authentication or authorization failure          | 401, 403             |
| `VALIDATION_ERROR` | Request payload validation failed                | 422                  |
| `BAD_REQUEST`      | Invalid request structure or parameters          | 400                  |
| `NOT_FOUND`        | Requested resource doesn't exist                 | 404                  |
| `CONFLICT`         | Resource conflict (e.g., duplicate unique field) | 409                  |
| `RATE_LIMIT`       | Rate limit exceeded                              | 429                  |
| `SERVER_ERROR`     | Unhandled server error                           | 500                  |

### Status Code Mapping

The `CoreErrorHandling` service automatically maps HTTP status codes to appropriate error codes:

```python
_CODE_MAP = {
    400: "BAD_REQUEST",
    401: "AUTH_FAILURE",
    403: "AUTH_FAILURE",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMIT",
}
```

## Exception Handling Architecture

### Global Exception Handlers

The `CoreErrorHandling` service provides centralized exception handling through FastAPI's global exception handlers. All handlers follow the same pattern:

1. Extract trace ID from request state
2. Create standardized `ErrorResponse`
3. Log error with appropriate severity
4. Return JSON response with consistent format

```python
class CoreErrorHandling:
    """Service for handling global exceptions in FastAPI applications."""

    def __init__(self, audit: Audit):
        self.audit = audit

    def _get_trace_id(self, request: Request) -> str:
        """Get trace ID from request state."""
        return getattr(request.state, "trace_id", "unknown")

    async def http_exception_handler(self, request: Request, exc: HTTPException) -> JSONResponse:
        """Handle HTTP exceptions with standardized response format."""
        trace_id = self._get_trace_id(request)
        code = self._CODE_MAP.get(exc.status_code, "ERROR")

        payload = ErrorResponse(
            detail=exc.detail,
            code=code,
            status_code=exc.status_code,
            trace_id=trace_id,
        ).model_dump()

        self.audit.error("http_exception", **payload)
        return JSONResponse(status_code=exc.status_code, content=payload)
```

### Exception Handler Flow

1. An exception is raised during request processing
2. FastAPI routes the exception to the appropriate handler
3. The handler:
   - Extracts the trace ID from the request
   - Creates a standardized `ErrorResponse`
   - Logs the error with the trace ID
   - Returns the JSON response to the client

### Domain-Specific Exceptions

The codebase uses domain-specific exceptions for business logic errors. These are defined in `app/domain/errors.py`:

```python
# app/domain/errors.py
class InvalidCredentialsError(Exception):
    """Raised when authentication credentials are invalid."""
    pass

class InactiveUserError(Exception):
    """Raised when a user account is inactive or disabled."""
    pass

class UnverifiedEmailError(Exception):
    """Raised when user email is not verified."""
    pass

class DuplicateError(Exception):
    """Raised when attempting to create a resource that already exists."""
    def __init__(self, field: str):
        self.field = field
        super().__init__(f"Duplicate {field}")
```

### Exception Handling in Endpoints

Endpoints should catch domain exceptions and convert them to appropriate HTTP exceptions:

```python
try:
    user = await Auth._auth_usecase.register(payload)
    return user
except DuplicateError as dup:
    Audit.error("User registration failed - duplicate field", duplicate_field=dup.field)
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"{dup.field} already exists",
    ) from dup
except Exception as exc:
    Audit.error("User registration failed", error=str(exc), exc_info=True)
    raise
```

## Request Tracing

### Trace ID Generation

Trace IDs are managed by the middleware system and extracted in error handlers:

```python
def _get_trace_id(self, request: Request) -> str:
    """Get trace ID from request state."""
    return getattr(request.state, "trace_id", "unknown")
```

The trace ID is:

1. Generated by middleware for each request
2. Stored in `request.state.trace_id`
3. Included in all error responses
4. Used for correlation in audit logs
5. Available in response headers for debugging

### Using Trace IDs for Debugging

When a client reports an error:

1. Ask for the `trace_id` from the error response
2. Search server logs for this ID to find all related log entries
3. Reconstruct the complete request flow and error context

## Audit Logging

### Error Audit Trail

The `CoreErrorHandling` service provides structured error logging with appropriate severity levels:

```python
# Different severity levels for different error types

# Error level: Unhandled exceptions, critical failures
self.audit.error("unhandled_exception", trace_id=trace_id, exc_info=exc)

# Warning level: Expected business logic failures
self.audit.warning("db_conflict", **payload)
self.audit.warning("weak_password", **payload)

# Error level: Authentication and authorization failures
self.audit.error("http_exception", **payload)
```

### Endpoint-Level Error Logging

Endpoints should include comprehensive audit logging for both success and failure scenarios:

```python
@staticmethod
@ep.post("/register")
async def register_user(request: Request, payload: UserCreate):
    client_ip = request.client.host or "unknown"

    Audit.info("User registration started", username=payload.username, client_ip=client_ip)

    try:
        user = await Auth._auth_usecase.register(payload)
        Audit.info("User registration completed", user_id=user.id, username=user.username)
        return user
    except DuplicateError as dup:
        Audit.error("User registration failed - duplicate", duplicate_field=dup.field)
        raise HTTPException(status_code=409, detail=f"{dup.field} already exists")
    except Exception as exc:
        Audit.error("User registration failed", error=str(exc), exc_info=True)
        raise
```

### Log Severity Levels

The audit logging system uses structured severity levels:

- **Error**: Unhandled exceptions, authentication failures, critical business logic failures
- **Warning**: Expected business conflicts (integrity errors), weak passwords, rate limiting
- **Info**: Successful operations, operation start/completion events

### Audit Event Naming Convention

Use consistent naming for audit events:

- Format: `{domain}_{operation}_{status}`
- Examples: `user_registration_started`, `wallet_creation_failed`, `auth_login_success`
- Include relevant context: `user_id`, `client_ip`, `duration_ms`, error details

## Frontend Error Handling Architecture

The React frontend implements a comprehensive error handling system that seamlessly integrates with the backend error response format. This section covers all aspects of frontend error handling, from React Error Boundaries to API error management.

### Table of Contents

1. [React Error Boundaries](#react-error-boundaries)
2. [API Error Handling Patterns](#api-error-handling-patterns)
3. [Form Validation and Error Display](#form-validation-and-error-display)
4. [User Notification System](#user-notification-system)
5. [Network Error Handling and Retry](#network-error-handling-and-retry)
6. [Error Logging and Monitoring](#error-logging-and-monitoring)
7. [Graceful Degradation Strategies](#graceful-degradation-strategies)
8. [Error Recovery Patterns](#error-recovery-patterns)
9. [TypeScript Error Handling](#typescript-error-handling)

## React Error Boundaries

### Error Boundary Implementation

The application uses a centralized `ErrorBoundary` component to catch and handle JavaScript errors in the component tree:

```typescript
// components/ErrorBoundary.tsx
import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Box, Typography, Button, Alert } from '@mui/material';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error for monitoring
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    // TODO: Send to error monitoring service
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <Box display="flex" flexDirection="column" alignItems="center" p={3}>
          <Alert severity="error" sx={{ mb: 2, maxWidth: 600 }}>
            <Typography variant="h6" gutterBottom>
              Something went wrong
            </Typography>
            <Typography variant="body2" gutterBottom>
              {this.state.error?.message || 'An unexpected error occurred'}
            </Typography>
            <Button variant="contained" onClick={this.handleReset} sx={{ mt: 2 }}>
              Try Again
            </Button>
          </Alert>
        </Box>
      );
    }

    return this.props.children;
  }
}
```

### Error Boundary Usage Patterns

1. **Application-level boundary**:

   ```typescript
   // App.tsx
   function App() {
     return (
       <ErrorBoundary>
         <Router>
           <Routes>
             {/* Your routes */}
           </Routes>
         </Router>
       </ErrorBoundary>
     );
   }
   ```

2. **Component-level boundaries**:

   ```typescript
   // For isolating errors in specific components
   function DashboardPage() {
     return (
       <div>
         <ErrorBoundary fallback={<div>Chart failed to load</div>}>
           <ChartComponent />
         </ErrorBoundary>
         <ErrorBoundary fallback={<div>Table failed to load</div>}>
           <DataTable />
         </ErrorBoundary>
       </div>
     );
   }
   ```

3. **Route-level boundaries**:
   ```typescript
   // Wrap routes that might have complex error scenarios
   <Route
     path="/wallet/:id"
     element={
       <ErrorBoundary>
         <WalletDetailPage />
       </ErrorBoundary>
     }
   />
   ```

### Error Boundary Best Practices

- **Granular Boundaries**: Use multiple error boundaries to isolate failures
- **Custom Fallbacks**: Provide context-specific fallback UI for different components
- **Error Recovery**: Include "Try Again" functionality where appropriate
- **Error Reporting**: Log errors to monitoring services in `componentDidCatch`
- **User Experience**: Ensure fallback UI maintains app navigation and core functionality

## API Error Handling Patterns

### Centralized API Client Configuration

The API client handles authentication, token refresh, and standardized error processing:

```typescript
// services/api.ts
import axios from "axios";

const apiClient = axios.create({
  baseURL: process.env.VITE_API_URL || "http://localhost:8000",
  withCredentials: true,
});

// Request interceptor for authentication
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// Response interceptor for error handling and token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Handle token refresh for 401 errors
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshResponse = await apiClient.post("/auth/refresh");
        const newToken = refreshResponse.data.access_token;

        localStorage.setItem("access_token", newToken);
        apiClient.defaults.headers.common["Authorization"] =
          `Bearer ${newToken}`;

        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem("access_token");
        localStorage.removeItem("session_active");
        window.location.href = "/login-register";
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  },
);
```

### Redux Async Thunk Error Handling

The application uses Redux Toolkit's `createAsyncThunk` with comprehensive error handling:

```typescript
// store/authSlice.ts
export const login = createAsyncThunk(
  "auth/login",
  async (
    credentials: { email: string; password: string },
    { rejectWithValue },
  ) => {
    try {
      const formData = new URLSearchParams();
      formData.append("username", credentials.email);
      formData.append("password", credentials.password);

      const tokenResponse = await apiClient.post("/auth/token", formData);
      const accessToken = tokenResponse.data?.access_token;

      if (accessToken) {
        localStorage.setItem("access_token", accessToken);
        apiClient.defaults.headers.common["Authorization"] =
          `Bearer ${accessToken}`;
      }

      const userResponse = await apiClient.get("/users/me");
      localStorage.setItem("session_active", "1");

      return userResponse.data as UserProfile;
    } catch (error: any) {
      if (axios.isAxiosError(error)) {
        return rejectWithValue({
          status: error.response?.status,
          data: error.response?.data,
          message: error.response?.data?.detail || error.message,
        });
      }
      throw error;
    }
  },
);

// Error handling in reducers
extraReducers: (builder) => {
  builder.addCase(login.rejected, (state, action) => {
    state.status = "failed";
    state.error = (action.payload as AuthError) || {
      message: action.error.message || "Login failed",
    };
  });
};
```

### Component-Level API Error Handling

Components handle API errors with user-friendly messaging and appropriate fallbacks:

```typescript
// Example from LoginRegisterPage.tsx
const handleLogin = async (e: React.FormEvent) => {
  e.preventDefault();
  try {
    await dispatch(
      login({ email: loginEmail, password: loginPassword }),
    ).unwrap();
    navigate("/dashboard");
  } catch (error: any) {
    const status = error?.status || error?.data?.status_code;
    const detail = error?.data?.detail;
    const code = error?.data?.code;

    if (!status) {
      setLoginError("Unable to reach server. Please check your connection.");
    } else if (status === 401) {
      setLoginError("Invalid email or password. Please try again.");
    } else if (status === 403 && code === "EMAIL_NOT_VERIFIED") {
      setLoginError("Please verify your email address before logging in.");
    } else {
      setLoginError(detail || "Login failed. Please try again.");
    }
  }
};
```

### Error Response Mapping

Map backend error codes to user-friendly messages:

```typescript
// utils/errorMessages.ts
export const ERROR_MESSAGES = {
  AUTH_FAILURE: "Invalid username or password. Please try again.",
  VALIDATION_ERROR: "Please check your input and try again.",
  BAD_REQUEST: "Invalid request. Please check your input.",
  NOT_FOUND: "The requested resource was not found.",
  CONFLICT: "This action conflicts with existing data.",
  RATE_LIMIT: "Too many attempts. Please try again later.",
  SERVER_ERROR: "Server error occurred. Please try again later.",
  NETWORK_ERROR: "Network error. Please check your connection.",
  INSUFFICIENT_BALANCE: "Insufficient balance for this transaction.",
  EMAIL_NOT_VERIFIED: "Please verify your email address first.",
} as const;

export const getErrorMessage = (error: any): string => {
  // Extract error code from backend response
  const code = error?.response?.data?.code || error?.data?.code;

  if (code && ERROR_MESSAGES[code as keyof typeof ERROR_MESSAGES]) {
    return ERROR_MESSAGES[code as keyof typeof ERROR_MESSAGES];
  }

  // Extract detail message from backend
  const detail = error?.response?.data?.detail || error?.data?.detail;
  if (detail) {
    return detail;
  }

  // Network errors
  if (!error?.response && error?.message) {
    return ERROR_MESSAGES.NETWORK_ERROR;
  }

  // Default fallback
  return "An unexpected error occurred. Please try again.";
};
```

## Form Validation and Error Display

### Form-Level Error Handling

Forms implement comprehensive validation with clear error messaging:

```typescript
// Example form component with validation
const TransferForm: React.FC = () => {
  const [formData, setFormData] = useState({ amount: '', recipient: '' });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.amount) {
      newErrors.amount = 'Amount is required';
    } else if (isNaN(Number(formData.amount))) {
      newErrors.amount = 'Amount must be a valid number';
    } else if (Number(formData.amount) <= 0) {
      newErrors.amount = 'Amount must be greater than 0';
    }

    if (!formData.recipient) {
      newErrors.recipient = 'Recipient address is required';
    } else if (!isValidAddress(formData.recipient)) {
      newErrors.recipient = 'Invalid wallet address format';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    setSubmitError('');

    try {
      await dispatch(transferFunds(formData)).unwrap();
      showNotification('Transfer completed successfully', { severity: 'success' });
      navigate('/wallet');
    } catch (error: any) {
      const errorMessage = getErrorMessage(error);
      setSubmitError(errorMessage);

      // Log trace ID for support
      const traceId = error?.response?.data?.trace_id;
      if (traceId) {
        console.error(`Transfer failed [${traceId}]:`, error);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <TextField
        label="Amount"
        value={formData.amount}
        onChange={e => setFormData(prev => ({ ...prev, amount: e.target.value }))}
        error={!!errors.amount}
        helperText={errors.amount}
        disabled={isSubmitting}
      />

      <TextField
        label="Recipient"
        value={formData.recipient}
        onChange={e => setFormData(prev => ({ ...prev, recipient: e.target.value }))}
        error={!!errors.recipient}
        helperText={errors.recipient}
        disabled={isSubmitting}
      />

      {submitError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {submitError}
        </Alert>
      )}

      <Button
        type="submit"
        disabled={isSubmitting}
        startIcon={isSubmitting ? <CircularProgress size={20} /> : undefined}
      >
        {isSubmitting ? 'Processing...' : 'Transfer'}
      </Button>
    </form>
  );
};
```

### Field-Level Validation Patterns

```typescript
// Custom validation hooks
const useFieldValidation = (value: string, validators: Validator[]) => {
  const [error, setError] = useState("");

  useEffect(() => {
    for (const validator of validators) {
      const result = validator(value);
      if (result !== true) {
        setError(result);
        return;
      }
    }
    setError("");
  }, [value, validators]);

  return error;
};

// Validator functions
const required = (value: string): string | true =>
  value.trim() ? true : "This field is required";

const email = (value: string): string | true =>
  /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value) ? true : "Invalid email format";

const minLength =
  (min: number) =>
  (value: string): string | true =>
    value.length >= min ? true : `Must be at least ${min} characters`;
```

## User Notification System

### Notification Architecture

The application uses a Redux-based notification system for user feedback:

```typescript
// store/notificationSlice.ts
interface Notification {
  id: string;
  message: string;
  severity: "success" | "error" | "warning" | "info";
  autoHideDuration?: number;
}

const notificationSlice = createSlice({
  name: "notification",
  initialState: { notifications: [] as Notification[] },
  reducers: {
    addNotification: (
      state,
      action: PayloadAction<Omit<Notification, "id">>,
    ) => {
      const id = Date.now().toString();
      state.notifications.push({ ...action.payload, id });
    },
    removeNotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter(
        (notification) => notification.id !== action.payload,
      );
    },
  },
});
```

### Notification Hook

Custom hook for easy notification management:

```typescript
// hooks/useNotification.ts
const useNotification = () => {
  const dispatch = useDispatch<AppDispatch>();

  const showNotification = (
    message: string,
    options: NotificationOptions = {},
  ) => {
    const { severity = "info", autoHideDuration = 6000 } = options;
    dispatch(addNotification({ message, severity, autoHideDuration }));
  };

  const showSuccess = (message: string, autoHideDuration?: number) => {
    showNotification(message, { severity: "success", autoHideDuration });
  };

  const showError = (message: string, autoHideDuration?: number) => {
    showNotification(message, { severity: "error", autoHideDuration });
  };

  const showWarning = (message: string, autoHideDuration?: number) => {
    showNotification(message, { severity: "warning", autoHideDuration });
  };

  return { showSuccess, showError, showWarning, showNotification };
};
```

### Toast Component

Material-UI based toast notifications:

```typescript
// components/Toast.tsx
const Toast: React.FC<ToastProps> = ({
  open,
  message,
  severity,
  onClose,
  autoHideDuration = 6000,
}) => (
  <Snackbar
    open={open}
    autoHideDuration={autoHideDuration}
    onClose={onClose}
    anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
  >
    <Alert onClose={onClose} severity={severity} sx={{ width: '100%' }}>
      {message}
    </Alert>
  </Snackbar>
);
```

### Notification Manager

Centralized notification rendering:

```typescript
// components/NotificationManager.tsx
const NotificationManager: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const notifications = useSelector((state: RootState) => state.notification.notifications);

  const handleClose = (id: string) => {
    dispatch(removeNotification(id));
  };

  return (
    <>
      {notifications.map(notification => (
        <Toast
          key={notification.id}
          open={true}
          message={notification.message}
          severity={notification.severity}
          onClose={() => handleClose(notification.id)}
          autoHideDuration={notification.autoHideDuration}
        />
      ))}
    </>
  );
};
```

## Network Error Handling and Retry

### Retry Mechanism

Implement exponential backoff for network operations:

```typescript
// utils/retry.ts
interface RetryOptions {
  maxAttempts: number;
  baseDelay: number;
  maxDelay: number;
  backoffFactor: number;
}

const defaultRetryOptions: RetryOptions = {
  maxAttempts: 3,
  baseDelay: 1000,
  maxDelay: 10000,
  backoffFactor: 2,
};

export const withRetry = async <T>(
  operation: () => Promise<T>,
  options: Partial<RetryOptions> = {},
): Promise<T> => {
  const { maxAttempts, baseDelay, maxDelay, backoffFactor } = {
    ...defaultRetryOptions,
    ...options,
  };

  let lastError: Error;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error as Error;

      // Don't retry on client errors (4xx) except 429
      if (axios.isAxiosError(error)) {
        const status = error.response?.status;
        if (status && status >= 400 && status < 500 && status !== 429) {
          throw error;
        }
      }

      if (attempt === maxAttempts) {
        break;
      }

      // Calculate delay with exponential backoff
      const delay = Math.min(
        baseDelay * Math.pow(backoffFactor, attempt - 1),
        maxDelay,
      );

      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }

  throw lastError!;
};
```

### Network Status Detection

Monitor network connectivity:

```typescript
// hooks/useNetworkStatus.ts
const useNetworkStatus = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [wasOffline, setWasOffline] = useState(false);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      if (wasOffline) {
        // Show reconnection notification
        showNotification("Connection restored", { severity: "success" });
        setWasOffline(false);
      }
    };

    const handleOffline = () => {
      setIsOnline(false);
      setWasOffline(true);
      showNotification("Connection lost. Some features may be unavailable.", {
        severity: "warning",
        autoHideDuration: 0, // Don't auto-hide
      });
    };

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, [wasOffline]);

  return isOnline;
};
```

### API Call with Retry

Wrapper for API calls with retry logic:

```typescript
// services/apiWithRetry.ts
export const apiCallWithRetry = async <T>(
  apiCall: () => Promise<AxiosResponse<T>>,
  options?: Partial<RetryOptions>,
): Promise<T> => {
  return withRetry(async () => {
    const response = await apiCall();
    return response.data;
  }, options);
};

// Usage example
const fetchWalletData = async (walletId: string) => {
  return apiCallWithRetry(() => apiClient.get(`/wallets/${walletId}`), {
    maxAttempts: 3,
    baseDelay: 2000,
  });
};
```

## Error Logging and Monitoring

### Error Logging Service

Centralized error logging with context:

```typescript
// services/errorLogger.ts
interface ErrorContext {
  userId?: string;
  component?: string;
  action?: string;
  metadata?: Record<string, any>;
}

class ErrorLogger {
  private static instance: ErrorLogger;

  static getInstance(): ErrorLogger {
    if (!ErrorLogger.instance) {
      ErrorLogger.instance = new ErrorLogger();
    }
    return ErrorLogger.instance;
  }

  logError(error: Error, context?: ErrorContext) {
    const errorData = {
      message: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      ...context,
    };

    // Log to console in development
    if (process.env.NODE_ENV === "development") {
      console.error("Error logged:", errorData);
    }

    // Send to monitoring service in production
    if (process.env.NODE_ENV === "production") {
      this.sendToMonitoringService(errorData);
    }
  }

  logApiError(error: any, context?: ErrorContext) {
    const apiErrorData = {
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      config: {
        method: error.config?.method,
        url: error.config?.url,
        data: error.config?.data,
      },
      traceId: error.response?.data?.trace_id,
      ...context,
    };

    this.logError(new Error(`API Error: ${error.message}`), apiErrorData);
  }

  private async sendToMonitoringService(errorData: any) {
    try {
      // Example: Send to Sentry, LogRocket, or custom endpoint
      await fetch("/api/errors", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(errorData),
      });
    } catch (err) {
      console.error("Failed to send error to monitoring service:", err);
    }
  }
}

export const errorLogger = ErrorLogger.getInstance();
```

### Integration with Error Boundary

Enhanced error boundary with logging:

```typescript
class ErrorBoundary extends Component<Props, State> {
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    errorLogger.logError(error, {
      component: "ErrorBoundary",
      metadata: { errorInfo, componentStack: errorInfo.componentStack },
    });
  }
}
```

### API Error Logging

Automatic logging of API errors:

```typescript
// In API interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    errorLogger.logApiError(error, {
      component: "ApiClient",
      action: "api_request",
    });
    return Promise.reject(error);
  },
);
```

## Graceful Degradation Strategies

### Loading States and Skeletons

Provide feedback during loading and error states:

```typescript
const WalletList: React.FC = () => {
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchWallets = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await apiCallWithRetry(() => apiClient.get('/wallets'));
        setWallets(data);
      } catch (err) {
        setError(getErrorMessage(err));
        errorLogger.logApiError(err, { component: 'WalletList', action: 'fetch_wallets' });
      } finally {
        setLoading(false);
      }
    };

    fetchWallets();
  }, []);

  if (loading) {
    return <WalletListSkeleton />;
  }

  if (error) {
    return (
      <Alert severity="error" action={
        <Button color="inherit" onClick={() => window.location.reload()}>
          Retry
        </Button>
      }>
        {error}
      </Alert>
    );
  }

  return <WalletTable wallets={wallets} />;
};
```

### Fallback UI Components

Create meaningful fallback experiences:

```typescript
const ChartFallback: React.FC<{ error?: string }> = ({ error }) => (
  <Box
    display="flex"
    flexDirection="column"
    alignItems="center"
    justifyContent="center"
    height={300}
    border="1px dashed #ccc"
    borderRadius={2}
    p={3}
  >
    <Typography variant="h6" color="textSecondary" gutterBottom>
      Chart Unavailable
    </Typography>
    <Typography variant="body2" color="textSecondary" textAlign="center">
      {error || 'Unable to load chart data at this time'}
    </Typography>
    <Button variant="outlined" onClick={() => window.location.reload()} sx={{ mt: 2 }}>
      Refresh Page
    </Button>
  </Box>
);
```

### Progressive Enhancement

Implement features that work without JavaScript:

```typescript
// Ensure forms work with basic HTML submission
const ContactForm: React.FC = () => {
  const [jsEnabled, setJsEnabled] = useState(false);

  useEffect(() => {
    setJsEnabled(true);
  }, []);

  return (
    <form
      method={jsEnabled ? undefined : "POST"}
      action={jsEnabled ? undefined : "/api/contact"}
      onSubmit={jsEnabled ? handleSubmit : undefined}
    >
      {/* Form fields */}
      <button type="submit">
        {jsEnabled ? 'Send Message' : 'Submit'}
      </button>
    </form>
  );
};
```

## Error Recovery Patterns

### Retry Mechanisms

User-controlled retry functionality:

```typescript
const useRetryableOperation = <T>(
  operation: () => Promise<T>,
  dependencies: any[] = []
) => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  const execute = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await operation();
      setData(result);
      setRetryCount(0);
    } catch (err) {
      setError(getErrorMessage(err));
      setRetryCount(prev => prev + 1);
    } finally {
      setLoading(false);
    }
  }, dependencies);

  const retry = () => {
    execute();
  };

  useEffect(() => {
    execute();
  }, dependencies);

  return { data, loading, error, retry, retryCount };
};

// Usage
const WalletBalanceCard: React.FC<{ walletId: string }> = ({ walletId }) => {
  const { data: balance, loading, error, retry } = useRetryableOperation(
    () => fetchWalletBalance(walletId),
    [walletId]
  );

  if (error) {
    return (
      <Card>
        <CardContent>
          <Alert severity="error" action={
            <Button size="small" onClick={retry}>
              Retry
            </Button>
          }>
            {error}
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        {loading ? <Skeleton height={60} /> : <BalanceDisplay balance={balance} />}
      </CardContent>
    </Card>
  );
};
```

### State Recovery

Restore application state after errors:

```typescript
// hooks/useErrorRecovery.ts
const useErrorRecovery = () => {
  const dispatch = useDispatch();

  const recoverFromError = useCallback(
    (errorType: string) => {
      switch (errorType) {
        case "AUTH_ERROR":
          dispatch(logout());
          navigate("/login");
          break;
        case "NETWORK_ERROR":
          // Retry last action or refresh data
          dispatch(refreshUserData());
          break;
        case "VALIDATION_ERROR":
          // Clear form errors, reset to valid state
          dispatch(clearFormErrors());
          break;
        default:
          // Generic recovery
          showNotification("Please refresh the page to continue", {
            severity: "info",
            autoHideDuration: 0,
          });
      }
    },
    [dispatch, navigate],
  );

  return { recoverFromError };
};
```

## TypeScript Error Handling

### Typed Error Handling

Strong typing for error handling patterns:

```typescript
// types/errors.ts
export interface ApiError {
  status: number;
  code: string;
  detail: string;
  trace_id: string;
}

export interface AsyncOperationState<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
}

export type ErrorCode = keyof typeof ERROR_MESSAGES;

export interface FormErrors<T> {
  [K in keyof T]?: string;
}
```

### Type-Safe Error Utilities

```typescript
// utils/typeGuards.ts
export const isApiError = (error: any): error is ApiError => {
  return (
    typeof error === "object" &&
    error !== null &&
    "status" in error &&
    "code" in error &&
    "detail" in error
  );
};

export const isNetworkError = (error: any): boolean => {
  return error?.message === "Network Error" || !error?.response;
};

export const isValidationError = (error: any): boolean => {
  return error?.response?.status === 422 || error?.code === "VALIDATION_ERROR";
};
```

### Generic Error Handler Hook

```typescript
// hooks/useErrorHandler.ts
interface ErrorHandlerOptions<T> {
  onError?: (error: ApiError) => void;
  fallbackData?: T;
  enableRetry?: boolean;
}

const useErrorHandler = <T>(
  asyncOperation: () => Promise<T>,
  options: ErrorHandlerOptions<T> = {},
) => {
  const [state, setState] = useState<AsyncOperationState<T>>({
    data: options.fallbackData || null,
    loading: false,
    error: null,
  });

  const { showError } = useNotification();

  const execute = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const result = await asyncOperation();
      setState({ data: result, loading: false, error: null });
      return result;
    } catch (error: any) {
      const apiError: ApiError = isApiError(error)
        ? error
        : {
            status: error?.response?.status || 500,
            code: error?.response?.data?.code || "UNKNOWN_ERROR",
            detail: getErrorMessage(error),
            trace_id: error?.response?.data?.trace_id || "unknown",
          };

      setState((prev) => ({ ...prev, loading: false, error: apiError }));

      if (options.onError) {
        options.onError(apiError);
      } else {
        showError(apiError.detail);
      }

      throw apiError;
    }
  }, [asyncOperation, options, showError]);

  return {
    ...state,
    execute,
    retry: options.enableRetry ? execute : undefined,
  };
};
```

## Client-Side Error Handling Best Practices

### Integration with Backend Error Format

1. **Check for standardized error envelope**:

   ```typescript
   try {
     const response = await apiClient.post("/auth/token", credentials);
     return response.data;
   } catch (error) {
     if (error.response?.data?.code === "AUTH_FAILURE") {
       // Handle authentication failure
     } else if (error.response?.data?.trace_id) {
       // Log the trace ID for support correlation
       console.error(
         `Error [${error.response.data.trace_id}]:`,
         error.response.data.detail,
       );
       errorLogger.logApiError(error, {
         traceId: error.response.data.trace_id,
       });
     }
     throw error;
   }
   ```

2. **Include trace IDs in support requests**:

   ```typescript
   const SupportForm: React.FC<{ error?: ApiError }> = ({ error }) => (
     <form onSubmit={handleSubmit}>
       {error?.trace_id && (
         <input type="hidden" name="traceId" value={error.trace_id} />
       )}
       <textarea
         name="description"
         placeholder="Describe what happened..."
         required
       />
       <button type="submit">Submit Support Request</button>
     </form>
   );
   ```

3. **Correlate frontend and backend logs**:
   ```typescript
   // Include trace ID in frontend error logs
   errorLogger.logError(new Error("Frontend operation failed"), {
     traceId: backendError?.trace_id,
     component: "TransferForm",
     action: "submit_transfer",
   });
   ```

## Testing Error Scenarios

### Frontend Testing

Test that React components handle errors correctly and display appropriate user feedback:

```typescript
// __tests__/components/LoginForm.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import LoginForm from '../components/LoginForm';
import authReducer from '../store/authSlice';
import notificationReducer from '../store/notificationSlice';

const createTestStore = () => configureStore({
  reducer: {
    auth: authReducer,
    notification: notificationReducer,
  },
});

describe('LoginForm Error Handling', () => {
  it('displays error message on authentication failure', async () => {
    // Mock API error response
    vi.spyOn(global, 'fetch').mockRejectedValueOnce({
      response: {
        status: 401,
        data: {
          detail: 'Invalid username or password',
          code: 'AUTH_FAILURE',
          status_code: 401,
          trace_id: '123e4567-e89b-12d3-a456-426614174000'
        }
      }
    });

    const store = createTestStore();
    render(
      <Provider store={store}>
        <LoginForm />
      </Provider>
    );

    // Submit form with invalid credentials
    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'test@example.com' }
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'wrongpassword' }
    });
    fireEvent.click(screen.getByRole('button', { name: 'Login' }));

    // Check that error is displayed
    await waitFor(() => {
      expect(screen.getByText('Invalid username or password')).toBeInTheDocument();
    });
  });

  it('handles network errors gracefully', async () => {
    // Mock network error
    vi.spyOn(global, 'fetch').mockRejectedValueOnce(new Error('Network Error'));

    const store = createTestStore();
    render(
      <Provider store={store}>
        <LoginForm />
      </Provider>
    );

    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'test@example.com' }
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'password123' }
    });
    fireEvent.click(screen.getByRole('button', { name: 'Login' }));

    await waitFor(() => {
      expect(screen.getByText(/unable to reach server/i)).toBeInTheDocument();
    });
  });

  it('shows loading state during form submission', async () => {
    // Mock delayed API response
    vi.spyOn(global, 'fetch').mockImplementationOnce(
      () => new Promise(resolve => setTimeout(resolve, 1000))
    );

    const store = createTestStore();
    render(
      <Provider store={store}>
        <LoginForm />
      </Provider>
    );

    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'test@example.com' }
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'password123' }
    });
    fireEvent.click(screen.getByRole('button', { name: 'Login' }));

    // Check loading state
    expect(screen.getByText('Logging in...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Login' })).toBeDisabled();
  });
});
```

### Error Boundary Testing

Test that error boundaries catch and display errors properly:

```typescript
// __tests__/components/ErrorBoundary.test.tsx
import React from 'react';
import { render, screen } from '@testing-library/react';
import ErrorBoundary from '../components/ErrorBoundary';

// Component that throws an error
const ProblemChild: React.FC<{ shouldError?: boolean }> = ({ shouldError = true }) => {
  if (shouldError) {
    throw new Error('Test error message');
  }
  return <div>Child component rendered successfully</div>;
};

describe('ErrorBoundary', () => {
  // Suppress console.error for these tests
  const originalError = console.error;
  beforeAll(() => {
    console.error = jesvit.fn();
  });
  afterAll(() => {
    console.error = originalError;
  });

  it('renders children when there is no error', () => {
    render(
      <ErrorBoundary>
        <ProblemChild shouldError={false} />
      </ErrorBoundary>
    );

    expect(screen.getByText('Child component rendered successfully')).toBeInTheDocument();
  });

  it('renders fallback UI when child throws error', () => {
    render(
      <ErrorBoundary>
        <ProblemChild />
      </ErrorBoundary>
    );

    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
    expect(screen.getByText('Test error message')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Try Again' })).toBeInTheDocument();
  });

  it('renders custom fallback when provided', () => {
    const customFallback = <div>Custom error fallback</div>;

    render(
      <ErrorBoundary fallback={customFallback}>
        <ProblemChild />
      </ErrorBoundary>
    );

    expect(screen.getByText('Custom error fallback')).toBeInTheDocument();
  });

  it('resets error state when Try Again is clicked', () => {
    const { rerender } = render(
      <ErrorBoundary>
        <ProblemChild />
      </ErrorBoundary>
    );

    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();

    // Click Try Again
    fireEvent.click(screen.getByRole('button', { name: 'Try Again' }));

    // Re-render with fixed component
    rerender(
      <ErrorBoundary>
        <ProblemChild shouldError={false} />
      </ErrorBoundary>
    );

    expect(screen.getByText('Child component rendered successfully')).toBeInTheDocument();
  });
});
```

### API Error Handling Testing

Test API error scenarios with different error codes:

```typescript
// __tests__/hooks/useErrorHandler.test.tsx
import { renderHook, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { store } from '../store';
import useErrorHandler from '../hooks/useErrorHandler';

const wrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <Provider store={store}>{children}</Provider>
);

describe('useErrorHandler', () => {
  it('handles successful API calls', async () => {
    const mockOperation = vi.fn().mockResolvedValue({ data: 'success' });

    const { result } = renderHook(
      () => useErrorHandler(mockOperation),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.data).toEqual({ data: 'success' });
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
    });
  });

  it('handles API errors with proper error mapping', async () => {
    const mockError = {
      response: {
        status: 422,
        data: {
          code: 'VALIDATION_ERROR',
          detail: 'Invalid input data',
          trace_id: 'test-trace-id'
        }
      }
    };

    const mockOperation = vi.fn().mockRejectedValue(mockError);

    const { result } = renderHook(
      () => useErrorHandler(mockOperation),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toEqual({
        status: 422,
        code: 'VALIDATION_ERROR',
        detail: 'Invalid input data',
        trace_id: 'test-trace-id'
      });
    });
  });

  it('provides retry functionality when enabled', async () => {
    const mockOperation = vi.fn()
      .mockRejectedValueOnce(new Error('Network Error'))
      .mockResolvedValueOnce({ data: 'success on retry' });

    const { result } = renderHook(
      () => useErrorHandler(mockOperation, { enableRetry: true }),
      { wrapper }
    );

    // First call fails
    await waitFor(() => {
      expect(result.current.error).toBeTruthy();
    });

    // Retry succeeds
    await result.current.retry!();

    await waitFor(() => {
      expect(result.current.data).toEqual({ data: 'success on retry' });
      expect(result.current.error).toBeNull();
    });
  });
});
```

### Form Validation Testing

Test form validation and error display:

```typescript
// __tests__/components/TransferForm.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TransferForm from '../components/TransferForm';

describe('TransferForm Validation', () => {
  it('shows validation errors for empty fields', async () => {
    render(<TransferForm />);

    // Submit empty form
    fireEvent.click(screen.getByRole('button', { name: 'Transfer' }));

    await waitFor(() => {
      expect(screen.getByText('Amount is required')).toBeInTheDocument();
      expect(screen.getByText('Recipient address is required')).toBeInTheDocument();
    });
  });

  it('validates amount field correctly', async () => {
    const user = userEvent.setup();
    render(<TransferForm />);

    const amountInput = screen.getByLabelText('Amount');

    // Test invalid amount
    await user.type(amountInput, 'invalid');
    fireEvent.blur(amountInput);

    await waitFor(() => {
      expect(screen.getByText('Amount must be a valid number')).toBeInTheDocument();
    });

    // Test negative amount
    await user.clear(amountInput);
    await user.type(amountInput, '-10');
    fireEvent.blur(amountInput);

    await waitFor(() => {
      expect(screen.getByText('Amount must be greater than 0')).toBeInTheDocument();
    });
  });

  it('clears validation errors when fields are corrected', async () => {
    const user = userEvent.setup();
    render(<TransferForm />);

    const amountInput = screen.getByLabelText('Amount');

    // Trigger validation error
    fireEvent.click(screen.getByRole('button', { name: 'Transfer' }));

    await waitFor(() => {
      expect(screen.getByText('Amount is required')).toBeInTheDocument();
    });

    // Fix the error
    await user.type(amountInput, '100');
    fireEvent.blur(amountInput);

    await waitFor(() => {
      expect(screen.queryByText('Amount is required')).not.toBeInTheDocument();
    });
  });
});
```

### Network Error Testing

Test network connectivity handling:

```typescript
// __tests__/hooks/useNetworkStatus.test.tsx
import { renderHook, act } from "@testing-library/react";
import useNetworkStatus from "../hooks/useNetworkStatus";

// Mock navigator.onLine
Object.defineProperty(navigator, "onLine", {
  writable: true,
  value: true,
});

describe("useNetworkStatus", () => {
  it("detects when going offline", () => {
    const { result } = renderHook(() => useNetworkStatus());

    expect(result.current).toBe(true);

    // Simulate going offline
    act(() => {
      Object.defineProperty(navigator, "onLine", { value: false });
      window.dispatchEvent(new Event("offline"));
    });

    expect(result.current).toBe(false);
  });

  it("detects when coming back online", () => {
    // Start offline
    Object.defineProperty(navigator, "onLine", { value: false });

    const { result } = renderHook(() => useNetworkStatus());

    expect(result.current).toBe(false);

    // Simulate coming online
    act(() => {
      Object.defineProperty(navigator, "onLine", { value: true });
      window.dispatchEvent(new Event("online"));
    });

    expect(result.current).toBe(true);
  });
});
```

### Notification System Testing

Test that notifications are displayed correctly:

```typescript
// __tests__/hooks/useNotification.test.tsx
import { renderHook } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import useNotification from '../hooks/useNotification';
import notificationReducer from '../store/notificationSlice';

const createTestStore = () => configureStore({
  reducer: { notification: notificationReducer },
});

describe('useNotification', () => {
  it('adds success notification to store', () => {
    const store = createTestStore();
    const wrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
      <Provider store={store}>{children}</Provider>
    );

    const { result } = renderHook(() => useNotification(), { wrapper });

    result.current.showSuccess('Operation completed successfully');

    const state = store.getState();
    expect(state.notification.notifications).toHaveLength(1);
    expect(state.notification.notifications[0]).toMatchObject({
      message: 'Operation completed successfully',
      severity: 'success',
    });
  });

  it('adds error notification with custom duration', () => {
    const store = createTestStore();
    const wrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
      <Provider store={store}>{children}</Provider>
    );

    const { result } = renderHook(() => useNotification(), { wrapper });

    result.current.showError('Operation failed', 10000);

    const state = store.getState();
    expect(state.notification.notifications[0]).toMatchObject({
      message: 'Operation failed',
      severity: 'error',
      autoHideDuration: 10000,
    });
  });
});
```

### Integration Testing

Test complete error flows from API to UI:

```typescript
// __tests__/integration/auth.integration.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import { Provider } from 'react-redux';
import { store } from '../store';
import LoginRegisterPage from '../pages/LoginRegisterPage';

// Mock API server
const server = setupServer(
  rest.post('/auth/token', (req, res, ctx) => {
    return res(
      ctx.status(401),
      ctx.json({
        detail: 'Invalid username or password',
        code: 'AUTH_FAILURE',
        status_code: 401,
        trace_id: 'test-trace-id'
      })
    );
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('Authentication Error Flow', () => {
  it('handles complete login error flow', async () => {
    render(
      <Provider store={store}>
        <LoginRegisterPage />
      </Provider>
    );

    // Fill in login form
    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'test@example.com' }
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'wrongpassword' }
    });

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: 'Login' }));

    // Verify error is displayed
    await waitFor(() => {
      expect(screen.getByText('Invalid username or password')).toBeInTheDocument();
    });

    // Verify form is still accessible for retry
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Login' })).toBeEnabled();
  });
});
```

### Backend Testing

Test that endpoints return proper error responses:

```python
# tests/domains/auth/integration/test_auth.py
async def test_login_invalid_credentials(client):
    response = await client.post(
        "/auth/token",
        data={"username": "invalid", "password": "wrong"}
    )

    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "AUTH_FAILURE"
    assert "trace_id" in data
    assert data["detail"] == "Invalid username or password"

async def test_login_unverified_email(client):
    # Create unverified user
    await client.post("/auth/register", json={
        "username": "test",
        "email": "test@example.com",
        "password": "password123"
    })

    response = await client.post(
        "/auth/token",
        data={"username": "test@example.com", "password": "password123"}
    )

    assert response.status_code == 403
    data = response.json()
    assert data["code"] == "EMAIL_NOT_VERIFIED"
    assert "trace_id" in data
```

## Summary

The React frontend error handling system provides a comprehensive, user-friendly approach to managing errors throughout the application. Key features include:

### 🛡️ **Robust Error Boundaries**

- Application-level and component-level error isolation
- Custom fallback UI for different contexts
- Error recovery mechanisms with "Try Again" functionality

### 🔗 **Seamless Backend Integration**

- Automatic token refresh handling
- Standardized error response processing
- Trace ID correlation for debugging support

### 📝 **Comprehensive Form Validation**

- Field-level and form-level validation
- Real-time error feedback
- User-friendly error messages

### 🔔 **Intelligent Notification System**

- Toast notifications for different severity levels
- Auto-hide functionality with custom durations
- Redux-based state management

### 🌐 **Network Resilience**

- Automatic retry with exponential backoff
- Network connectivity monitoring
- Graceful degradation strategies

### 📊 **Error Monitoring & Logging**

- Centralized error logging service
- Context-rich error reporting
- Integration with monitoring services

### 🔄 **Recovery Patterns**

- User-controlled retry mechanisms
- State restoration after errors
- Progressive enhancement support

### 🎯 **TypeScript Safety**

- Strong typing for error handling patterns
- Type guards for error classification
- Generic error handling utilities

This comprehensive error handling system ensures that users receive clear, actionable feedback while providing developers with the tools needed to diagnose and resolve issues effectively. The integration between frontend and backend error handling creates a seamless experience for both users and support teams.

---

_Last updated: 2025-07-19_
