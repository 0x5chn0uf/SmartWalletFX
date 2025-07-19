# Security Patterns for Claude Code

This document outlines the security patterns and implementations used in the trading bot codebase. These patterns ensure proper authentication, authorization, and data protection.

## JWT Token Rotation Patterns

### Overview

The application implements automated JWT key rotation using a Redis-distributed lock pattern with Celery tasks for scalability and reliability.

### Implementation Pattern

#### 1. Key Rotation State Machine

```python
# Pure functional approach for key rotation decisions
from app.utils.jwt_rotation import promote_and_retire_keys, KeySet

def decide_rotation(current_keys: KeySet, now: datetime) -> KeySetUpdate:
    """Pure function that decides which keys to promote/retire"""
    return promote_and_retire_keys(current_keys, now)
```

#### 2. Distributed Lock Pattern

```python
# Redis-based distributed locking for single-worker execution
@asynccontextmanager
async def acquire_lock(redis: Redis, lock_name: str, timeout: int):
    lock_key = f"lock:{lock_name}"
    lock_acquired = await redis.set(lock_key, "locked", nx=True, ex=timeout)
    try:
        yield lock_acquired
    finally:
        if lock_acquired:
            await redis.delete(lock_key)
```

#### 3. Automated Rotation Task

```python
# Celery task with exponential backoff
@celery.task(bind=True)
def promote_and_retire_keys_task(self):
    async def _run():
        async with acquire_lock(redis, "jwt_key_rotation", timeout=300) as got_lock:
            if not got_lock:
                return  # Another worker is handling rotation

            key_set = _gather_current_key_set()
            update = promote_and_retire_keys(key_set, datetime.now(timezone.utc))
            if not update.is_noop():
                _apply_key_set_update(update)

    try:
        asyncio.run(_run())
    except Exception as exc:
        retry_delay = min(60 * 60, (self.request.retries + 1) * 60)
        raise self.retry(exc=exc, countdown=retry_delay)
```

#### 4. Grace Period Management

```python
# Retired keys remain valid during grace period
_RETIRED_KEYS: dict[str, datetime] = {}

def rotate_signing_key(new_kid: str, new_signing_key: str, config: Configuration):
    old_kid = config.ACTIVE_JWT_KID
    config.JWT_KEYS[new_kid] = new_signing_key
    config.ACTIVE_JWT_KID = new_kid

    if old_kid and old_kid != new_kid:
        retire_at = datetime.now(timezone.utc) + timedelta(
            seconds=config.JWT_ROTATION_GRACE_PERIOD_SECONDS
        )
        _RETIRED_KEYS[old_kid] = retire_at
```

### Key Implementation Rules for Claude Code

1. **Always use distributed locks** for rotation tasks in multi-worker environments
2. **Implement grace periods** to prevent token invalidation during rotation
3. **Use pure functions** for rotation logic to enable reliable testing
4. **Include retry mechanisms** with exponential backoff for transient failures
5. **Invalidate caches** after key rotation to ensure immediate propagation

## RBAC Implementation Details

### Role-Based Access Control Structure

```python
class UserRole(str, Enum):
    ADMIN = "admin"
    TRADER = "trader"
    FUND_MANAGER = "fund_manager"
    INDIVIDUAL_INVESTOR = "individual_investor"

class Permission(str, Enum):
    WALLET_READ = "wallet:read"
    WALLET_WRITE = "wallet:write"
    PORTFOLIO_READ = "portfolio:read"
    DEFI_WRITE = "defi:write"
    ADMIN_SYSTEM = "admin:system"
```

### Permission Mapping Pattern

```python
# Static mapping from roles to permissions
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    UserRole.ADMIN.value: [
        Permission.WALLET_READ.value,
        Permission.WALLET_WRITE.value,
        Permission.ADMIN_SYSTEM.value,
        # ... all permissions
    ],
    UserRole.INDIVIDUAL_INVESTOR.value: [
        Permission.WALLET_READ.value,
        Permission.PORTFOLIO_READ.value,
        # ... read-only permissions
    ]
}
```

### Authorization Helper Functions

```python
def has_permission(user_roles: List[str], required_permission: str) -> bool:
    """Check if user has specific permission based on roles"""
    user_permissions = get_permissions_for_roles(user_roles)
    return required_permission in user_permissions

def get_permissions_for_roles(roles: List[str]) -> List[str]:
    """Get all permissions for a list of roles"""
    permissions = set()
    for role in roles:
        if role in ROLE_PERMISSIONS:
            permissions.update(ROLE_PERMISSIONS[role])
    return list(permissions)
```

### Claude Code RBAC Implementation Guidelines

1. **Use enums** for roles and permissions to ensure type safety
2. **Implement centralized permission mapping** rather than scattered checks
3. **Support multiple roles per user** for flexible authorization
4. **Provide helper functions** for common authorization patterns
5. **Validate roles and permissions** at the API boundary

## Rate Limiting Configurations

### In-Memory Rate Limiter Pattern

```python
class InMemoryRateLimiter:
    def __init__(self, max_attempts: int, window_seconds: int):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._hits: DefaultDict[str, List[float]] = defaultdict(list)

    def allow(self, key: str) -> bool:
        now = time()
        window_start = now - self.window_seconds
        hits = [ts for ts in self._hits[key] if ts >= window_start]
        self._hits[key] = hits  # prune old hits

        if len(hits) >= self.max_attempts:
            return False
        hits.append(now)
        return True
```

### Rate Limiter Integration

```python
class RateLimiterUtils:
    def __init__(self, config: Configuration):
        self.__login_rate_limiter = InMemoryRateLimiter(
            max_attempts=config.AUTH_RATE_LIMIT_ATTEMPTS,
            window_seconds=config.AUTH_RATE_LIMIT_WINDOW_SECONDS,
        )

    @property
    def login_rate_limiter(self) -> InMemoryRateLimiter:
        return self.__login_rate_limiter
```

### Usage in Endpoints

```python
# Apply rate limiting before authentication
if not rate_limiter.allow(client_ip):
    raise HTTPException(
        status_code=429,
        detail="Too many login attempts. Please try again later."
    )
```

### Production Rate Limiting Guidelines for Claude Code

1. **Use Redis-based rate limiting** in production environments
2. **Apply rate limiting by IP address** for brute force protection
3. **Implement sliding window algorithms** for more accurate limiting
4. **Configure different limits** for different endpoints (login vs. API calls)
5. **Include rate limit headers** in responses for client awareness

## Encryption Utility Usage

### GPG Encryption Pattern

```python
class EncryptionUtils:
    def __init__(self, config: Configuration):
        self.__config = config

    def encrypt_file(self, file_path: Path, *, recipient: str = None) -> Path:
        recipient_key = recipient or self.__config.GPG_RECIPIENT_KEY_ID
        if not recipient_key:
            raise EncryptionError("GPG_RECIPIENT_KEY_ID not configured")

        encrypted_path = file_path.with_suffix(file_path.suffix + ".gpg")
        cmd = [
            "gpg", "--batch", "--yes",
            "--recipient", recipient_key,
            "--output", str(encrypted_path),
            "--encrypt", str(file_path)
        ]

        subprocess.run(cmd, check=True, capture_output=True)
        return encrypted_path
```

### Encryption Integration Examples

```python
# Encrypt sensitive data before storage/transmission
encryption_utils = EncryptionUtils(config)
encrypted_backup = encryption_utils.encrypt_file(
    Path("/tmp/user_data.json"),
    recipient="admin@example.com"
)
```

### Claude Code Encryption Guidelines

1. **Use external GPG binary** to minimize dependency footprint
2. **Configure recipient keys** via environment variables
3. **Always verify file existence** before encryption
4. **Handle subprocess errors** gracefully with meaningful messages
5. **Return encrypted file paths** for further processing
6. **Never store encryption keys** in source code

## React Frontend Security Patterns

### Overview

The React frontend implements a comprehensive security architecture that integrates with the backend authentication system while providing client-side protection against common web vulnerabilities.

### Frontend Authentication State Management

#### 1. Redux-Based Authentication State

```typescript
// Centralized authentication state management
interface AuthState {
  isAuthenticated: boolean;
  user: UserProfile | null;
  status: "idle" | "loading" | "succeeded" | "failed";
  error: AuthError | null;
}

export const fetchCurrentUser = createAsyncThunk(
  "auth/fetchCurrentUser",
  async () => {
    const resp = await apiClient.get("/users/me", { withCredentials: true });
    localStorage.setItem("session_active", "1");
    return resp.data as UserProfile;
  },
);
```

#### 2. Secure Session Management Pattern

```typescript
// Silent session refresh with evidence-based checks
const hasSessionEvidence = localStorage.getItem("session_active") === "1";

if (hasSessionEvidence) {
  dispatch(sessionCheckStarted());

  apiClient
    .post("/auth/refresh", {}, { withCredentials: true })
    .then((resp) => {
      const newToken = resp.data?.access_token;
      if (newToken) {
        apiClient.defaults.headers.common["Authorization"] =
          `Bearer ${newToken}`;
        localStorage.setItem("access_token", newToken);
        dispatch(fetchCurrentUser());
      }
    })
    .catch(() => {
      localStorage.removeItem("session_active");
      dispatch(sessionCheckFinished());
    });
}
```

### Secure Token Storage and Handling

#### 1. JWT Token Management Strategy

```typescript
// Secure token storage with automatic cleanup
export const logoutUser = createAsyncThunk("auth/logout", async () => {
  try {
    await apiClient.post("/auth/logout", {}, { withCredentials: true });
  } catch (error) {
    console.warn(
      "Backend logout failed, clearing frontend state anyway:",
      error,
    );
  }
  delete apiClient.defaults.headers.common["Authorization"];
  localStorage.removeItem("session_active");
  localStorage.removeItem("access_token");
});
```

#### 2. Automatic Token Refresh Implementation

```typescript
// Response interceptor with refresh token loop prevention
let isRefreshing = false;

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const isAuthEndpoint = originalRequest.url?.includes("/auth/");
    const hasAuthHeader = Boolean(originalRequest.headers?.Authorization);
    const hasActiveSession = localStorage.getItem("session_active") === "1";

    if (
      error.response?.status === 401 &&
      hasAuthHeader &&
      hasActiveSession &&
      !isRefreshing &&
      !isAuthEndpoint
    ) {
      isRefreshing = true;
      // Perform refresh logic
    }
  },
);
```

### Route Protection and Authorization

#### 1. Protected Route Component Pattern

```typescript
interface ProtectedRouteProps {
  children: React.ReactElement;
  roles?: string[];
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, roles }) => {
  const { isAuthenticated, status, user } = useSelector((state: RootState) => state.auth);

  if (status === 'loading' || status === 'idle') {
    return null; // Wait for auth resolution
  }

  if (!isAuthenticated) {
    return <Navigate to="/login-register" replace />;
  }

  if (roles && user && !roles.includes(user.role)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return children;
};
```

#### 2. Role-Based Access Control Integration

```typescript
// Route protection with role validation
<Route
  path="/admin"
  element={
    <ProtectedRoute roles={['admin']}>
      <AdminDashboard />
    </ProtectedRoute>
  }
/>
```

### Input Sanitization and Validation Security

#### 1. Form Input Validation Pattern

```typescript
// Client-side validation with secure error handling
const handleRegister = async (e: React.FormEvent) => {
  e.preventDefault();

  if (registerPassword !== registerConfirm) {
    setRegisterError("Passwords do not match");
    return;
  }

  // Additional client-side validation
  if (registerPassword.length < 8) {
    setRegisterError("Password must be at least 8 characters");
    return;
  }

  try {
    await dispatch(
      registerUser({
        email: registerEmail,
        password: registerPassword,
      }),
    ).unwrap();
  } catch (err: any) {
    const status = err?.status ?? err?.response?.status;
    if (status === 400) {
      setRegisterError("Password does not meet strength requirements");
    } else if (status === 409) {
      setRegisterError("Email already registered");
    }
  }
};
```

#### 2. HTML Input Security

```typescript
// Secure form inputs with proper attributes
<Input
  type="email"
  id="register-email"
  name="email"
  placeholder="Enter your email"
  value={registerEmail}
  onChange={e => setRegisterEmail(e.target.value)}
  required
  autoComplete="email"
/>
```

### XSS Protection Strategies

#### 1. React's Built-in XSS Protection

```typescript
// React automatically escapes content - safe by default
const UserProfile: React.FC<{ user: UserProfile }> = ({ user }) => (
  <div>
    <h1>Welcome, {user.username}!</h1> {/* Automatically escaped */}
    <p>Email: {user.email}</p> {/* Automatically escaped */}
  </div>
);
```

#### 2. Dangerous Content Handling

```typescript
// When HTML content must be rendered, use DOMPurify
import DOMPurify from 'dompurify';

const SafeHtmlContent: React.FC<{ content: string }> = ({ content }) => (
  <div
    dangerouslySetInnerHTML={{
      __html: DOMPurify.sanitize(content)
    }}
  />
);
```

### CSRF Protection Implementation

#### 1. SameSite Cookie Configuration

```typescript
// API client configured for CSRF protection
const apiClient = axios.create({
  baseURL: API_URL,
  withCredentials: true, // Include SameSite cookies
});
```

#### 2. Double Submit Cookie Pattern

```typescript
// CSRF token handling in requests
apiClient.interceptors.request.use(
  (config) => {
    const csrfToken = document
      .querySelector('meta[name="csrf-token"]')
      ?.getAttribute("content");
    if (csrfToken) {
      config.headers["X-CSRF-Token"] = csrfToken;
    }
    return config;
  },
  (error) => Promise.reject(error),
);
```

### Content Security Policy Configuration

#### 1. CSP Headers Implementation

```html
<!-- Strict CSP configuration in index.html -->
<meta
  http-equiv="Content-Security-Policy"
  content="
  default-src 'self';
  script-src 'self' 'unsafe-inline' https://apis.google.com;
  style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
  font-src 'self' https://fonts.gstatic.com;
  img-src 'self' data: https:;
  connect-src 'self' https://api.github.com https://accounts.google.com;
  frame-src https://accounts.google.com;
"
/>
```

#### 2. CSP Violation Reporting

```typescript
// CSP violation reporting endpoint
window.addEventListener("securitypolicyviolation", (event) => {
  console.warn("CSP Violation:", event.violatedDirective, event.blockedURI);
  // Report to monitoring service
  fetch("/api/csp-report", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      violatedDirective: event.violatedDirective,
      blockedURI: event.blockedURI,
      documentURI: event.documentURI,
    }),
  });
});
```

### Secure API Communication Patterns

#### 1. Environment-Based Configuration

```typescript
// Secure API URL configuration
const API_URL =
  (import.meta as any).env.VITE_API_URL || "http://localhost:8000";

// Validate API URL in production
if (import.meta.env.PROD && !API_URL.startsWith("https://")) {
  throw new Error("Production API must use HTTPS");
}
```

#### 2. Request/Response Validation

```typescript
// Type-safe API responses with validation
interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

const validateApiResponse = <T>(response: any): ApiResponse<T> => {
  if (!response.data) {
    throw new Error("Invalid API response format");
  }
  return response;
};
```

### OAuth Security Best Practices

#### 1. Secure OAuth Flow Implementation

```typescript
// OAuth button with secure redirect handling
export const OAuthButton: React.FC<Props> = ({ provider }) => {
  const handleClick = () => {
    // Validate API URL before redirect
    if (!API_URL.startsWith('https://') && import.meta.env.PROD) {
      throw new Error('OAuth requires HTTPS in production');
    }

    // Generate state parameter for CSRF protection
    const state = crypto.getRandomValues(new Uint32Array(4)).join('');
    sessionStorage.setItem('oauth_state', state);

    window.location.href = `${API_URL}/auth/oauth/${provider}/login?state=${state}`;
  };

  return (
    <button onClick={handleClick} type="button">
      Continue with {provider}
    </button>
  );
};
```

#### 2. OAuth Callback Validation

```typescript
// OAuth callback state validation
useEffect(() => {
  const urlParams = new URLSearchParams(window.location.search);
  const state = urlParams.get("state");
  const storedState = sessionStorage.getItem("oauth_state");

  if (state && storedState && state === storedState) {
    sessionStorage.removeItem("oauth_state");
    // Process OAuth callback
  } else if (state) {
    // Invalid state - potential CSRF attack
    console.error("OAuth state mismatch");
    navigate("/login-register?error=oauth_failed");
  }
}, []);
```

### Client-Side Security Monitoring

#### 1. Error Boundary Security

```typescript
class SecurityErrorBoundary extends React.Component {
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log security-relevant errors
    if (error.message.includes('CSP') || error.message.includes('XSS')) {
      fetch('/api/security-incident', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          error: error.message,
          stack: error.stack,
          timestamp: new Date().toISOString(),
          userAgent: navigator.userAgent,
        }),
      });
    }
  }

  render() {
    if (this.state.hasError) {
      return <div>Something went wrong. Please refresh the page.</div>;
    }
    return this.props.children;
  }
}
```

#### 2. Performance and Security Monitoring

```typescript
// Monitor for suspicious activity patterns
const useSecurityMonitoring = () => {
  useEffect(() => {
    let loginAttempts = 0;
    const maxAttempts = 5;

    const handleFailedLogin = () => {
      loginAttempts++;
      if (loginAttempts >= maxAttempts) {
        // Temporarily disable login form
        console.warn("Too many failed login attempts");
        // Could implement temporary account lockout UI
      }
    };

    // Reset counter on successful login
    const handleSuccessfulLogin = () => {
      loginAttempts = 0;
    };

    return () => {
      // Cleanup monitoring
    };
  }, []);
};
```

### Frontend Security Guidelines for Claude Code

1. **Always validate authentication state** before rendering protected content
2. **Use TypeScript** for type safety and reduce runtime errors
3. **Implement proper error boundaries** to catch and handle security exceptions
4. **Validate all user inputs** on both client and server sides
5. **Use HTTPS in production** for all API communications
6. **Implement CSP headers** to prevent XSS attacks
7. **Store sensitive data securely** using appropriate browser APIs
8. **Monitor for security violations** and implement incident reporting
9. **Use secure OAuth flows** with state validation
10. **Keep dependencies updated** and audit for vulnerabilities

## Security Best Practices Summary

### For JWT Implementation

- Implement automatic key rotation with distributed locking
- Use grace periods to prevent service disruption
- Include comprehensive audit logging
- Validate all JWT claims including required fields

### For RBAC Systems

- Use type-safe enums for roles and permissions
- Centralize permission mapping logic
- Support hierarchical permission inheritance
- Validate authorization at API boundaries

### For Rate Limiting

- Apply different limits for different endpoint types
- Use distributed rate limiting in production
- Include client feedback via response headers
- Implement progressive penalties for repeated violations

### For Data Encryption

- Use established encryption tools (GPG)
- Manage keys through secure configuration
- Encrypt sensitive data at rest and in transit
- Implement proper error handling for encryption failures

### For Frontend Security

- Implement secure authentication state management with Redux
- Use automatic token refresh with loop prevention
- Apply role-based route protection at the component level
- Validate all user inputs with client-side and server-side checks
- Configure strict Content Security Policy headers
- Use secure OAuth flows with state parameter validation
- Monitor for security violations and implement incident reporting
- Keep all dependencies updated and regularly audit for vulnerabilities
