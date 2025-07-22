# Dependency Injection System

> **Audience**: Claude Code and contributors working with dependency injection patterns
> **Purpose**: Complete guide to the custom DI container managing singletons across the hexagonal architecture

## Overview

The trading bot backend implements a custom dependency injection (DI) container that manages singleton instances and their dependencies. The system supports constructor injection with explicit dependency declarations and provides excellent testability through dependency substitution.

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [DIContainer Architecture](#dicontainer-architecture)
3. [Dependency Lifecycle](#dependency-lifecycle)
4. [Adding New Components](#adding-new-components)
5. [Testing with DI](#testing-with-di)
6. [Common Patterns](#common-patterns)
7. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)

## Core Concepts

### Why Dependency Injection?

Our DI system provides several benefits:

- **Decoupling**: Components depend on abstractions, not concrete implementations
- **Testability**: Easy substitution of real implementations with mocks/stubs
- **Lifecycle Management**: Centralized singleton instantiation and configuration
- **Explicit Dependencies**: Constructor injection makes dependencies clear and traceable

### Container Categories

The DIContainer organizes dependencies into distinct categories with dedicated storage and access methods:

```python
class DIContainer:
    def __init__(self):
        self._core = {}           # Core infrastructure
        self._services = {}       # Cross-cutting services  
        self._repositories = {}   # Data access layer
        self._usecases = {}      # Business logic
        self._endpoints = {}     # API transport layer
        self._utilities = {}     # Helper tools
```

**Category Details**:
- **Core**: Configuration, database, logging, error handling, middleware
- **Repositories**: Data persistence with database and audit dependencies
- **Services**: Email, OAuth, and other cross-cutting concerns
- **Usecases**: Business logic orchestrators depending on repositories and services
- **Endpoints**: FastAPI router classes using singleton pattern
- **Utilities**: JWT, encryption, rate limiting, password hashing tools

## DIContainer Architecture

### Initialization Sequence

The container follows a strict initialization order managed by dedicated initialization methods:

```python
def __init__(self):
    self._initialize_core()        # 1. Core infrastructure
    self._initialize_utilities()   # 2. Helper utilities  
    self._initialize_repositories() # 3. Data access
    self._initialize_services()    # 4. Cross-cutting services
    self._initialize_usecases()    # 5. Business logic
    self._initialize_endpoints()   # 6. API endpoints
```

**Dependency Flow**:
1. **Core**: Self-contained infrastructure (config, database, audit, logging)
2. **Utilities**: Depend only on core components
3. **Repositories**: Depend on database and audit from core
4. **Services**: Depend on repositories, utilities, and core components
5. **Usecases**: Depend on repositories, services, utilities, and core
6. **Endpoints**: Depend primarily on usecases

### Singleton Management

The DIContainer implements strict singleton management where each component is instantiated exactly once:

```python
# Registration pattern
def register_repository(self, name: str, repository):
    """Register a repository instance."""
    self._repositories[name] = repository

def get_repository(self, name: str):
    """Get a repository instance by name."""
    repository = self._repositories.get(name)
    if not repository:
        raise ValueError(f"Repository '{name}' not found.")
    return repository
```

**Singleton Guarantees**:
- Each component is created once during container initialization
- Dependencies are injected at construction time
- No lazy loading - all components are eager singletons
- Thread-safe access (all creation happens during startup)
- Fail-fast behavior with clear error messages for missing dependencies

## Dependency Lifecycle

### Container Creation

The container is typically created in one of two places:

1. **Application Startup**: In `main.py`, the container bootstraps the entire application
2. **Testing**: In test fixtures, where it may be populated with mocks

```python
# Application startup (main.py)
di_container = DIContainer()
app_factory = ApplicationFactory(di_container)
app = app_factory.create_app()

# Testing (conftest.py)
@pytest.fixture
def di_container():
    container = DIContainer()
    # Override with mocks as needed
    return container
```

### Component Registration

Components are registered using type-specific methods during initialization:

```python
# Core component registration
def _initialize_core(self):
    config = Configuration()
    self.register_core("config", config)
    
    audit = Audit()
    self.register_core("audit", audit)
    
    database = CoreDatabase(config, audit)
    self.register_core("database", database)

# Repository registration with dependencies
def _initialize_repositories(self):
    database = self.get_core("database")
    audit = self.get_core("audit")
    
    user_repository = UserRepository(database, audit)
    self.register_repository("user", user_repository)
    
    wallet_repository = WalletRepository(database, audit)
    self.register_repository("wallet", wallet_repository)
```

### Component Retrieval

Components are retrieved using the corresponding getter method:

```python
# Retrieval methods
config = self.get_core("config")
user_repo = self.get_repository("user")
email_service = self.get_service("email")
auth_usecase = self.get_usecase("auth")
jwt_utils = self.get_utility("jwt_utils")
auth_endpoint = self.get_endpoint("auth")
```

## Adding New Components

### Adding a New Repository

Follow the established pattern for repository dependency injection:

```python
# 1. Create repository class with standard dependencies
# app/repositories/transaction_repository.py
class TransactionRepository:
    """Repository for transaction persistence operations."""
    
    def __init__(self, database: CoreDatabase, audit: Audit):
        self.__database = database
        self.__audit = audit
    
    async def get_by_wallet_id(self, wallet_id: uuid.UUID) -> List[Transaction]:
        self.__audit.info("transaction_repository_get_by_wallet_started", wallet_id=str(wallet_id))
        # Implementation...
        
# 2. Import in di.py
from app.repositories.transaction_repository import TransactionRepository

# 3. Initialize and register in _initialize_repositories()
def _initialize_repositories(self):
    database = self.get_core("database")
    audit = self.get_core("audit")
    
    # Existing repositories...
    
    transaction_repository = TransactionRepository(database, audit)
    self.register_repository("transaction", transaction_repository)
```

### Adding a New Usecase

1. Create the usecase class in `app/usecase/`
2. Add it to the imports in `di.py`
3. Initialize and register it in `_initialize_usecases()`

```python
# 1. Create usecase class
# app/usecase/new_usecase.py
class NewUsecase:
    def __init__(self, repository, config, audit):
        self.repository = repository
        self.config = config
        self.audit = audit
        
# 2. Import in di.py
from app.usecase.new_usecase import NewUsecase

# 3. Initialize and register
def _initialize_usecases(self):
    # ...existing code...
    
    # Get dependencies
    config = self.get_core("config")
    audit = self.get_core("audit")
    new_repo = self.get_repository("new")
    
    # Create and register
    new_usecase = NewUsecase(new_repo, config, audit)
    self.register_usecase("new", new_usecase)
```

### Adding a New Endpoint

Endpoints use the singleton pattern with dependency injection:

```python
# 1. Create endpoint class using singleton pattern
# app/api/endpoints/transactions.py
from fastapi import APIRouter, Request, status
from app.api.dependencies import get_user_id_from_request
from app.usecase.transaction_usecase import TransactionUsecase
from app.utils.logging import Audit

class Transactions:
    """Transactions endpoint using singleton pattern with dependency injection."""
    
    ep = APIRouter(prefix="/transactions", tags=["transactions"])
    _transaction_uc: TransactionUsecase
    
    def __init__(self, transaction_usecase: TransactionUsecase):
        """Initialize with injected dependencies."""
        Transactions._transaction_uc = transaction_usecase
    
    @staticmethod
    @ep.get("/wallet/{wallet_id}")
    async def get_wallet_transactions(request: Request, wallet_id: str):
        """Get transactions for a wallet."""
        user_id = get_user_id_from_request(request)
        return await Transactions._transaction_uc.get_wallet_transactions(user_id, wallet_id)
        
# 2. Import and register in di.py
from app.api.endpoints.transactions import Transactions

def _initialize_endpoints(self):
    # Get dependencies
    transaction_uc = self.get_usecase("transaction")
    
    # Create and register
    transactions_endpoint = Transactions(transaction_uc)
    self.register_endpoint("transactions", transactions_endpoint)
```

## Testing with DI

### Mocking Dependencies

The DI system makes testing straightforward by allowing dependency substitution:

```python
# Example test with mocked dependencies
@pytest.fixture
def mock_user_repo():
    return MagicMock(spec=UserRepository)

@pytest.fixture
def auth_usecase(mock_user_repo, mock_email_service):
    config = Configuration()  # Use real config or mock
    audit = MagicMock(spec=Audit)
    return AuthUsecase(
        mock_user_repo, 
        mock_email_service,
        config,
        audit
    )

def test_auth_usecase_login(auth_usecase, mock_user_repo):
    # Test with mocked dependencies
    mock_user_repo.get_by_email.return_value = User(...)
    result = await auth_usecase.login(...)
    assert result.token is not None
```

### Using DIContainer in Tests

For integration tests, you can use a real DIContainer with selective mocking:

```python
@pytest.fixture
async def di_container():
    container = DIContainer()
    
    # Override specific components with mocks
    mock_email_service = MagicMock(spec=EmailService)
    container._services["email"] = mock_email_service
    
    return container

@pytest.fixture
async def auth_usecase(di_container):
    return di_container.get_usecase("auth")

async def test_registration_flow(auth_usecase, di_container):
    # Test using the container with mocked components
    mock_email = di_container.get_service("email")
    mock_email.send_verification.return_value = True
    
    result = await auth_usecase.register(...)
    assert result.user_id is not None
    mock_email.send_verification.assert_called_once()
```

## Common Patterns

### Standard Component Dependencies

Follow these established patterns for consistent dependency injection:

```python
# Repository pattern (always these two dependencies)
class ExampleRepository:
    def __init__(self, database: CoreDatabase, audit: Audit):
        self.__database = database
        self.__audit = audit

# Usecase pattern (repositories + services + core)
class ExampleUsecase:
    def __init__(
        self,
        example_repo: ExampleRepository,
        email_service: EmailService,
        config: Configuration,
        audit: Audit,
    ):
        # Store dependencies

# Service pattern (varies by service needs)
class ExampleService:
    def __init__(
        self,
        user_repo: UserRepository,
        jwt_utils: JWTUtils,
        config: Configuration,
        audit: Audit,
    ):
        # Store dependencies

# Endpoint pattern (primarily usecases, sometimes utilities)
class ExampleEndpoint:
    def __init__(self, example_usecase: ExampleUsecase, rate_limiter: RateLimiterUtils):
        ExampleEndpoint._usecase = example_usecase
        ExampleEndpoint._rate_limiter = rate_limiter
```

### Dependency Order Convention

Consistently order constructor parameters for readability:

```python
# Standard dependency order
def __init__(
    self,
    # 1. Repositories (data layer)
    user_repo: UserRepository,
    wallet_repo: WalletRepository,
    
    # 2. Services (cross-cutting)
    email_service: EmailService,
    oauth_service: OAuthService,
    
    # 3. Utilities (helpers)
    jwt_utils: JWTUtils,
    rate_limiter: RateLimiterUtils,
    
    # 4. Core components (infrastructure)
    config: Configuration,
    audit: Audit,
):
    # Store dependencies with consistent naming
    self.__user_repo = user_repo
    self.__wallet_repo = wallet_repo
    self.__email_service = email_service
    self.__oauth_service = oauth_service
    self.__jwt_utils = jwt_utils
    self.__rate_limiter = rate_limiter
    self.__config = config
    self.__audit = audit
```

## Anti-Patterns to Avoid

### ❌ Direct Instantiation

Never instantiate dependencies manually; always retrieve from the container:

```python
# BAD - Manual instantiation breaks singleton pattern
def _initialize_usecases(self):
    config = Configuration()  # Wrong! Creates new instance
    jwt_utils = JWTUtils(config, Audit())  # Wrong! Not using container

# GOOD - Use container dependencies
def _initialize_usecases(self):
    config = self.get_core("config")  # Correct! Reuses singleton
    jwt_utils = self.get_utility("jwt_utils")  # Correct! From container
    
    auth_usecase = AuthUsecase(user_repo, email_service, jwt_utils, config, audit)
    self.register_usecase("auth", auth_usecase)
```

### ❌ Circular Dependencies

Avoid circular dependencies between components. If you find yourself needing this, reconsider your design:

```python
# BAD: UserService needs AuthService which needs UserService
class UserService:
    def __init__(self, auth_service): ...

class AuthService:
    def __init__(self, user_service): ...
```

### ❌ Global State

Don't use global variables or module-level singletons. Everything should be managed by the DIContainer:

```python
# BAD
global_config = Configuration()

# GOOD
config = di_container.get_core("config")
```

### ❌ Service Locator Pattern

Never pass the container to components; use explicit dependency injection:

```python
# BAD - Service locator anti-pattern
class AuthUsecase:
    def __init__(self, di_container: DIContainer):
        self.user_repo = di_container.get_repository("user")  # Hidden dependency
        self.email_service = di_container.get_service("email")

# GOOD - Explicit dependency injection
class AuthUsecase:
    def __init__(
        self,
        user_repo: UserRepository,      # Clear, testable dependency
        email_service: EmailService,    # Easy to mock in tests
        config: Configuration,
        audit: Audit,
    ):
        self.__user_repo = user_repo
        self.__email_service = email_service
        self.__config = config
        self.__audit = audit
```

---

*Last updated: 2025-07-19* 