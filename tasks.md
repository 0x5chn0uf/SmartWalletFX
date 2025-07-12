# Task 50: Refactor Infrastructure and Root-Level Helpers from Module-Level Singletons to Explicit Class Instances

## Overview

This task involves refactoring the application's infrastructure components and root-level helpers from module-level singletons to explicit class instances. This will improve dependency injection, testability, and maintainability by eliminating global state and making dependencies explicit.

## Requirements Analysis

After analyzing the codebase, we've identified several module-level singletons and global variables that need to be refactored:

1. **Core Infrastructure Components**:
   - `database.py`: Contains global engine, SessionLocal, and Base instances
   - `config.py`: Contains global settings
   - `logging.py`: Contains global logging setup
   - `middleware.py`: Contains global middleware functions
   - `error_handling.py`: Contains global exception handlers

2. **Root-Level Helpers**:
   - `di.py`: Contains global dependency injection helpers
   - `celery_app.py`: Contains global Celery instance
   - `main.py`: Contains global FastAPI app creation

3. **Other Global Components**:
   - API routers in `api/endpoints/` modules
   - Rate limiters and other stateful utilities

4. **Application Layer Components**:
   - Usecases in `usecase/` modules that currently receive dependencies through constructors
   - Repositories in `repositories/` modules that currently receive database sessions through constructors

## Architecture Considerations

The refactoring will follow these architectural principles:

1. **Singleton Pattern**: Each usecase, repository, and endpoint will be a singleton instance created once at application startup
2. **Explicit Dependency Injection**: All dependencies will be explicitly passed through constructors at singleton creation time
3. **Single Responsibility**: Each class will have a clear, single responsibility
4. **Testability**: All components will be designed for easy mocking and testing through constructor injection
5. **Thread Safety**: Singleton instances will be thread-safe as they're created once and shared across requests
6. **Performance**: Singleton pattern eliminates the overhead of creating new instances for each request
7. **Clean Break**: Since there's no dev environment, we can make breaking changes without backward compatibility concerns

### Benefits of the Singleton Pattern:

1. **Memory Efficiency**: Only one instance of each component exists in memory
2. **Initialization Cost**: Dependencies are resolved once at startup, not per request
3. **Consistency**: All parts of the application use the same configured instances
4. **Debugging**: Easier to trace issues since there's only one instance of each component
5. **Configuration**: All configuration is done once at startup, ensuring consistency

## Implementation Strategy

We'll adopt a phased approach to minimize disruption, implementing a **singleton pattern** for each component:

### Phase 1: Core Infrastructure Classes

1. Create class-based versions of core infrastructure components as singletons
2. Implement the DIContainer to manage singleton lifecycle
3. Update existing code to use the singleton instances via dependency injection

### Phase 2: Repository Singleton Refactoring

1. Refactor ALL repositories to use explicit dependency injection through constructors
2. Each repository becomes a singleton instance created once by the DIContainer
3. Repositories receive their dependencies (DatabaseService, Audit) at construction time

### Phase 3: Usecase Singleton Refactoring

1. Refactor ALL usecases to use explicit dependency injection through constructors
2. Each usecase becomes a singleton instance created once by the DIContainer
3. Usecases receive their dependencies (repositories, services) at construction time

### Phase 4: API Endpoint Singleton Refactoring

1. Convert ALL API endpoints to class-based implementations following the Pings example
2. Each endpoint becomes a singleton instance created once by the DIContainer
3. Endpoints receive their dependencies (usecases) at construction time
4. Update API router registration in main.py to use singleton instances

### Phase 5: Root-Level Helper Classes

1. Refactor root-level helpers into class-based singleton implementations
2. Update references to use the singleton instances from DIContainer
3. Remove old module-level implementations completely

### Phase 6: Test Refactoring

1. Refactor ALL existing tests to use the new singleton dependency injection pattern
2. Update test fixtures to create mock singleton instances
3. Ensure all tests properly mock dependencies injected through constructors
4. Update integration tests to use the DIContainer for proper dependency wiring

### Phase 7: Utilities and Miscellaneous Components

1. Refactor remaining global utilities into class-based singleton implementations
2. Update references throughout the codebase to use singleton instances

## Detailed Implementation Steps

### 1. Database Infrastructure Refactoring

```python
# Current implementation (module-level singletons)
engine = create_async_engine(...)
SessionLocal = async_sessionmaker(...)
Base = declarative_base()

# New implementation (class-based)
class DatabaseService:
    def __init__(self, config):
        self.config = config
        self._setup_engine()
        self._setup_session_factory()

    def _setup_engine(self):
        # Logic to create engine based on config
        self.engine = create_async_engine(...)

    def _setup_session_factory(self):
        self.session_factory = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def get_session(self):
        async with self.session_factory() as session:
            yield session

    # For synchronous operations
    def get_sync_session(self):
        return self.sync_session_factory()
```

### 2. Configuration Service Refactoring

```python
# Current implementation (module-level singleton)
settings = Settings()

# New implementation (class-based)
class ConfigurationService:
    def __init__(self):
        self.settings = Settings()

    @property
    def project_name(self):
        return self.settings.PROJECT_NAME

    # Other properties and methods
```

### 3. FastAPI Application Factory Refactoring

```python
# Current implementation (module-level function)
def create_app() -> FastAPI:
    # App creation logic

app = create_app()

# New implementation (singleton-based with DIContainer)
class ApplicationFactory:
    def __init__(self, di_container: DIContainer):
        self.di_container = di_container

    def create_app(self) -> FastAPI:
        config_service = self.di_container.get_service("config")
        database_service = self.di_container.get_service("database")

        app = FastAPI(
            title=config_service.project_name,
            version=config_service.version,
            openapi_url="/openapi.json",
        )

        # Set up CORS, middleware, exception handlers

        # Use database_service for DB initialization
        @app.on_event("startup")
        async def on_startup() -> None:
            await database_service.init_db()

        # Register singleton endpoint routers
        self._register_routers(app)

        return app

    def _register_routers(self, app: FastAPI):
        # Get singleton endpoint instances from DIContainer
        email_verification_endpoint = self.di_container.get_endpoint("email_verification")
        wallet_endpoint = self.di_container.get_endpoint("wallet")
        oauth_endpoint = self.di_container.get_endpoint("oauth")

        # Register the singleton endpoint routers
        app.include_router(email_verification_endpoint.ep)
        app.include_router(wallet_endpoint.ep)
        app.include_router(oauth_endpoint.ep)
        # Add other endpoint routers...

# Usage in main.py
di_container = DIContainer()  # Creates all singletons
app_factory = ApplicationFactory(di_container)
app = app_factory.create_app()
```

### 4. Celery Service Refactoring

```python
# Current implementation (module-level singleton)
celery = Celery(...)
celery.conf.timezone = "UTC"
celery.conf.beat_schedule = {...}

# New implementation (class-based)
class CeleryService:
    def __init__(self, config_service):
        self.config_service = config_service
        self._setup_celery()

    def _setup_celery(self):
        self.celery = Celery(
            self.config_service.project_name,
            broker=self.config_service.celery_broker_url,
            backend=self.config_service.celery_backend_url,
        )
        self.celery.conf.timezone = "UTC"
        self._setup_beat_schedule()

    def _setup_beat_schedule(self):
        self.celery.conf.beat_schedule = {
            # Task definitions
        }

    @property
    def app(self):
        return self.celery
```

### 5. API Router Classes Refactoring

Following the Pings example, we'll refactor API routers to use class-based implementations with explicit dependency injection:

```python
# Example for email_verification.py
class EmailVerification:
    ep = APIRouter(prefix="/auth", tags=["auth"])
    __verification_uc: EmailVerificationUsecase

    def __init__(self, verification_usecase: EmailVerificationUsecase):
        EmailVerification.__verification_uc = verification_usecase

    @staticmethod
    @ep.post("/verify-email", response_model=TokenResponse)
    async def verify_email(payload: EmailVerificationVerify):
        return await EmailVerification.__verification_uc.verify_email(payload.token)

    @staticmethod
    @ep.post(
        "/resend-verification",
        status_code=status.HTTP_204_NO_CONTENT,
        response_class=Response,
        response_model=None,
    )
    async def resend_verification_email(
        payload: EmailVerificationRequest,
        background_tasks: BackgroundTasks,
    ) -> Response:
        await EmailVerification.__verification_uc.resend_verification(
            payload.email, background_tasks, verify_rate_limiter
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
```

### 6. Usecase and Repository Refactoring

Current usecases and repositories are instantiated directly in endpoints with minimal dependencies. We'll refactor them to use explicit dependency injection through constructors, similar to the endpoint pattern:

```python
# Current implementation (minimal dependencies)
class EmailVerificationUsecase:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._ev_repo = EmailVerificationRepository(session)
        self._user_repo = UserRepository(session)
        self._rt_repo = RefreshTokenRepository(session)

# New implementation (explicit dependency injection)
class EmailVerificationUsecase:
    def __init__(
        self,
        ev_repo: EmailVerificationRepository,
        user_repo: UserRepository,
        rt_repo: RefreshTokenRepository,
        email_service: EmailService,
        jwt_utils: JWTUtils,
        config_service: ConfigurationService,
        log: Log,
    ):
        self.__ev_repo = ev_repo
        self.__user_repo = user_repo
        self.__rt_repo = rt_repo
        self.__email_service = email_service
        self.__jwt_utils = jwt_utils
        self.__config_service = config_service
        self.__audit = audit

    async def verify_email(self, ctx: Context, token: str) -> TokenResponse:
        self.__audit.info("verify_email_started", token=token[:8] + "..." if len(token) > 8 else token)

        try:
            token_obj = await self.__ev_repo.get_valid(token)
            if not token_obj:
                self.__audit.warning("invalid_email_verification_token")
                raise HTTPException(status_code=400, detail="Invalid or expired token")

            user = await self.__user_repo.get_by_id(token_obj.user_id)
            if not user:
                self.__audit.error("user_not_found_for_verification", user_id=str(token_obj.user_id))
                raise HTTPException(status_code=400, detail="User not found")

            # Business logic continues...
                         self.__audit.info("email_verification_success", user_id=str(user.id))
             return tokens
         except Exception as e:
             self.__audit.error("email_verification_failed", error=str(e))
            raise
```

#### 7.3 Complete Repository Refactoring Structure

All repositories need to be refactored to use explicit dependency injection. Here are the complete list:

**All Repositories to Refactor:**

- `UserRepository` - User CRUD operations
- `EmailVerificationRepository` - Email verification token management
- `OAuthAccountRepository` - OAuth account management
- `PasswordResetRepository` - Password reset token management
- `RefreshTokenRepository` - JWT refresh token management
- `WalletRepository` - Wallet CRUD operations
- `PortfolioSnapshotRepository` - Portfolio snapshot management
- `HistoricalBalanceRepository` - Historical balance tracking
- `TokenRepository` - Token management
- `TokenPriceRepository` - Token price data
- `TokenBalanceRepository` - Token balance operations

```python
# Current repository pattern
class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

# New repository pattern (explicit dependency injection)
class UserRepository:
    def __init__(
        self,
        database_service: DatabaseService,
        audit: Audit,
    ):
        self.__database_service = database_service
        self.__audit = audit

    async def get_by_id(self, ctx: Context, user_id: str) -> Optional[User]:
        self.__audit.info("user_repository_get_by_id_started", user_id=user_id)

        try:
            async with self.__database_service.get_session() as session:
                if isinstance(user_id, str):
                    try:
                        user_id = uuid.UUID(user_id)
                    except ValueError:
                        pass

                user = await session.get(User, user_id)
                self.__audit.info("user_repository_get_by_id_success", user_id=user_id)
                return user
        except Exception as e:
            self.__audit.error("user_repository_get_by_id_failed", user_id=user_id, error=str(e))
            raise

# Similar pattern for WalletRepository
class WalletRepository:
    def __init__(
        self,
        database_service: DatabaseService,
        audit: Audit,
    ):
        self.__database_service = database_service
        self.__audit = audit

    async def create(self, ctx: Context, address: str, user_id: str, name: str) -> WalletResponse:
        self.__audit.info("wallet_repository_create_started", address=address, user_id=user_id)

        try:
            async with self.__database_service.get_session() as session:
                # Repository logic here
                self.__audit.info("wallet_repository_create_success", address=address, user_id=user_id)
                return result
        except Exception as e:
            self.__audit.error("wallet_repository_create_failed", address=address, user_id=user_id, error=str(e))
            raise

# Similar pattern for TokenPriceRepository
class TokenPriceRepository:
    def __init__(
        self,
        database_service: DatabaseService,
        audit: Audit,
    ):
        self.__database_service = database_service
        self.__audit = audit

    async def get_by_id(self, ctx: Context, token_id: str) -> Optional[TokenPrice]:
        self.__audit.info("token_price_repository_get_by_id_started", token_id=token_id)

        try:
            async with self.__database_service.get_session() as session:
                # Repository logic here
                self.__audit.info("token_price_repository_get_by_id_success", token_id=token_id)
                return result
        except Exception as e:
            self.__audit.error("token_price_repository_get_by_id_failed", token_id=token_id, error=str(e))
            raise
```

### 7. Complete Usecase Refactoring Structure

All usecases need to be refactored to use explicit dependency injection. Here are the complete list and their refactoring approach:

#### 7.1 All Usecases to Refactor:

- `EmailVerificationUsecase` - Email verification and resend functionality
- `WalletUsecase` - Wallet management and portfolio operations
- `OAuthUsecase` - OAuth authentication flows
- `TokenPriceUsecase` - Token price management
- `TokenUsecase` - Token operations
- `HistoricalBalanceUsecase` - Historical balance tracking
- `TokenBalanceUsecase` - Token balance operations
- `PortfolioSnapshotUsecase` - Portfolio snapshot management

#### 7.2 Example Refactoring Pattern:

```python
# Current pattern (example: WalletUsecase)
class WalletUsecase:
    def __init__(self, db: AsyncSession, current_user: User):
        self.db = db
        self.user = current_user
        self.wallet_repository = WalletRepository(db)
        self.portfolio_snapshot_repository = PortfolioSnapshotRepository(db)

# New pattern (explicit dependency injection)
class WalletUsecase:
    def __init__(
        self,
        wallet_repo: WalletRepository,
        portfolio_snapshot_repo: PortfolioSnapshotRepository,
        config_service: ConfigurationService,
        audit: Audit,
    ):
        self.__wallet_repo = wallet_repo
        self.__portfolio_snapshot_repo = portfolio_snapshot_repo
        self.__config_service = config_service
        self.__audit = audit

    async def create_wallet(self, ctx: Context, user: User, wallet: WalletCreate) -> WalletResponse:
        self.__audit.info("wallet_usecase_create_wallet_started", user_id=str(user.id), wallet_address=wallet.address)

        try:
            result = await self.__wallet_repo.create(
                ctx, address=wallet.address, user_id=user.id, name=wallet.name
            )
            self.__audit.info("wallet_usecase_create_wallet_success", user_id=str(user.id), wallet_id=str(result.id))
            return result
        except Exception as e:
            self.__audit.error("wallet_usecase_create_wallet_failed", user_id=str(user.id), error=str(e))
            raise

# Similar pattern for TokenPriceUsecase
class TokenPriceUsecase:
    def __init__(
        self,
        token_price_repo: TokenPriceRepository,
        config_service: ConfigurationService,
        audit: Audit,
    ):
        self.__token_price_repo = token_price_repo
        self.__config_service = config_service
        self.__audit = audit

    async def get_token_price(self, ctx: Context, token_id: str) -> TokenPrice:
        self.__audit.info("token_price_usecase_get_token_price_started", token_id=token_id)

        try:
            result = await self.__token_price_repo.get_by_id(ctx, token_id)
            self.__audit.info("token_price_usecase_get_token_price_success", token_id=token_id)
            return result
        except Exception as e:
            self.__audit.error("token_price_usecase_get_token_price_failed", token_id=token_id, error=str(e))
            raise

# Similar pattern for OAuthUsecase
class OAuthUsecase:
    def __init__(
        self,
        oauth_account_repo: OAuthAccountRepository,
        user_repo: UserRepository,
        refresh_token_repo: RefreshTokenRepository,
        config_service: ConfigurationService,
        audit: Audit,
    ):
        self.__oauth_account_repo = oauth_account_repo
        self.__user_repo = user_repo
        self.__refresh_token_repo = refresh_token_repo
        self.__config_service = config_service
        self.__audit = audit
```

### 8. Singleton Pattern Implementation

Each usecase, repository, and endpoint will be implemented as a singleton that gets initialized once with all its dependencies. The DIContainer will create and manage these singleton instances:

```python
class DIContainer:
    def __init__(self):
        self._services = {}
        self._repositories = {}
        self._usecases = {}
        self._endpoints = {}
        self._initialize_services()

    def _initialize_services(self):
        # Create and register core services (these can be singletons too)
        config_service = ConfigurationService()
        self.register_service("config", config_service)

        database_service = DatabaseService(config_service)
        self.register_service("database", database_service)

        # Use existing Audit service from app.utils.logging
        from app.utils.logging import Audit
        self.register_service("audit", Audit)

        email_service = EmailService(config_service)
        self.register_service("email", email_service)

        jwt_utils = JWTUtils(config_service)
        self.register_service("jwt_utils", jwt_utils)

        # Create and register singleton repositories
        self._initialize_repositories()

        # Create and register singleton usecases
        self._initialize_usecases()

        # Create and register singleton endpoints
        self._initialize_endpoints()

    def _initialize_repositories(self):
        database_service = self.get_service("database")
        log_service = self.get_service("log")

        # Initialize ALL repositories with explicit dependency injection
        user_repo = UserRepository(database_service, log_service)
        self.register_repository("user", user_repo)

        email_verification_repo = EmailVerificationRepository(database_service, log_service)
        self.register_repository("email_verification", email_verification_repo)

        oauth_account_repo = OAuthAccountRepository(database_service, log_service)
        self.register_repository("oauth_account", oauth_account_repo)

        password_reset_repo = PasswordResetRepository(database_service, log_service)
        self.register_repository("password_reset", password_reset_repo)

        refresh_token_repo = RefreshTokenRepository(database_service, log_service)
        self.register_repository("refresh_token", refresh_token_repo)

        wallet_repo = WalletRepository(database_service, log_service)
        self.register_repository("wallet", wallet_repo)

        portfolio_snapshot_repo = PortfolioSnapshotRepository(database_service, log_service)
        self.register_repository("portfolio_snapshot", portfolio_snapshot_repo)

        historical_balance_repo = HistoricalBalanceRepository(database_service, log_service)
        self.register_repository("historical_balance", historical_balance_repo)

        token_repo = TokenRepository(database_service, log_service)
        self.register_repository("token", token_repo)

        token_price_repo = TokenPriceRepository(database_service, log_service)
        self.register_repository("token_price", token_price_repo)

        token_balance_repo = TokenBalanceRepository(database_service, log_service)
        self.register_repository("token_balance", token_balance_repo)

    def _initialize_usecases(self):
        # Get required services and repositories
        config_service = self.get_service("config")
        email_service = self.get_service("email")
        jwt_utils = self.get_service("jwt_utils")
        log_service = self.get_service("log")

        # Get ALL repositories
        user_repo = self.get_repository("user")
        email_verification_repo = self.get_repository("email_verification")
        oauth_account_repo = self.get_repository("oauth_account")
        password_reset_repo = self.get_repository("password_reset")
        refresh_token_repo = self.get_repository("refresh_token")
        wallet_repo = self.get_repository("wallet")
        portfolio_snapshot_repo = self.get_repository("portfolio_snapshot")
        historical_balance_repo = self.get_repository("historical_balance")
        token_repo = self.get_repository("token")
        token_price_repo = self.get_repository("token_price")
        token_balance_repo = self.get_repository("token_balance")

        # Create and register ALL usecases
        email_verification_uc = EmailVerificationUsecase(
            email_verification_repo,
            user_repo,
            refresh_token_repo,
            email_service,
            jwt_utils,
            config_service,
            log_service,
        )
        self.register_usecase("email_verification", email_verification_uc)

        wallet_uc = WalletUsecase(
            wallet_repo,
            portfolio_snapshot_repo,
            config_service,
            log_service,
        )
        self.register_usecase("wallet", wallet_uc)

        oauth_uc = OAuthUsecase(
            oauth_account_repo,
            user_repo,
            refresh_token_repo,
            config_service,
            log_service,
        )
        self.register_usecase("oauth", oauth_uc)

        token_price_uc = TokenPriceUsecase(
            token_price_repo,
            config_service,
            log_service,
        )
        self.register_usecase("token_price", token_price_uc)

        token_uc = TokenUsecase(
            token_repo,
            config_service,
            log_service,
        )
        self.register_usecase("token", token_uc)

        historical_balance_uc = HistoricalBalanceUsecase(
            historical_balance_repo,
            config_service,
            log_service,
        )
        self.register_usecase("historical_balance", historical_balance_uc)

        token_balance_uc = TokenBalanceUsecase(
            token_balance_repo,
            token_repo,
            config_service,
            log_service,
        )
        self.register_usecase("token_balance", token_balance_uc)

        portfolio_snapshot_uc = PortfolioSnapshotUsecase(
            portfolio_snapshot_repo,
            wallet_repo,
            config_service,
            log_service,
        )
        self.register_usecase("portfolio_snapshot", portfolio_snapshot_uc)

    def _initialize_endpoints(self):
        # Get required usecases for endpoints
        email_verification_uc = self.get_usecase("email_verification")
        wallet_uc = self.get_usecase("wallet")
        oauth_uc = self.get_usecase("oauth")

        # Create and register singleton endpoints
        email_verification_endpoint = EmailVerification(email_verification_uc)
        self.register_endpoint("email_verification", email_verification_endpoint)

        wallet_endpoint = WalletEndpoint(wallet_uc)
        self.register_endpoint("wallet", wallet_endpoint)

        oauth_endpoint = OAuthEndpoint(oauth_uc)
        self.register_endpoint("oauth", oauth_endpoint)

        # Add other endpoints as needed...

    def register_service(self, name, service):
        self._services[name] = service

    def register_repository(self, name, repository):
        self._repositories[name] = repository

    def register_usecase(self, name, usecase):
        self._usecases[name] = usecase

    def register_endpoint(self, name, endpoint):
        self._endpoints[name] = endpoint

    def get_service(self, name):
        return self._services.get(name)

    def get_repository(self, name):
        return self._repositories.get(name)

    def get_usecase(self, name):
        return self._usecases.get(name)

    def get_endpoint(self, name):
        return self._endpoints.get(name)


```

## Dependencies

- No external dependencies are required for this refactoring
- All changes will be made within the existing codebase

## Challenges & Mitigations

1. **Challenge**: Managing the complete refactoring scope
   **Mitigation**: Implement the refactoring incrementally, with thorough testing at each step

2. **Challenge**: Thread safety for shared instances
   **Mitigation**: Implement proper thread-safety mechanisms using locks or thread-local storage

3. **Challenge**: Testing the refactored components
   **Mitigation**: Write comprehensive unit tests for each refactored class

4. **Challenge**: Ensuring all dependencies are properly wired
   **Mitigation**: Use comprehensive unit tests and integration tests to verify dependency injection

## Testing Strategy

### 1. **Unit Test Refactoring**

All existing unit tests need to be refactored to work with the new singleton dependency injection pattern:

```python
# Current test pattern (direct instantiation)
@pytest.fixture
def user_repository(db_session):
    return UserRepository(db_session)

def test_get_user_by_id(user_repository):
    # Test logic
    pass

# New test pattern (mock dependency injection)
@pytest.fixture
def mock_database_service():
    return Mock(spec=DatabaseService)

@pytest.fixture
def mock_audit():
    return Mock(spec=Audit)

@pytest.fixture
def user_repository(mock_database_service, mock_audit):
    return UserRepository(mock_database_service, mock_audit)

def test_get_user_by_id(user_repository, mock_database_service, mock_audit):
    # Setup mocks
    mock_database_service.get_session.return_value.__aenter__.return_value = Mock()

    # Test logic with proper mocking
    # Verify audit calls
    mock_audit.info.assert_called_with("user_repository_get_by_id_started", user_id="test_id")
```

### 2. **Integration Test Refactoring**

Integration tests need to use the DIContainer for proper dependency wiring:

```python
# Current integration test pattern
@pytest.fixture
def app():
    return create_app()

# New integration test pattern
@pytest.fixture
def di_container():
    return DIContainer()

@pytest.fixture
def app(di_container):
    app_factory = ApplicationFactory(di_container)
    return app_factory.create_app()

def test_email_verification_endpoint(app, di_container):
    # Test can access singleton instances if needed
    email_verification_uc = di_container.get_usecase("email_verification")
    # Test logic
```

### 3. **Test Categories to Refactor**

**Unit Tests (ALL need refactoring):**

- `tests/unit/repositories/` - All repository tests
- `tests/unit/usecase/` - All usecase tests
- `tests/unit/api/` - All endpoint tests
- `tests/unit/core/` - Core service tests

**Integration Tests (ALL need refactoring):**

- `tests/integration/api/` - All API endpoint integration tests
- `tests/integration/repositories/` - Repository integration tests
- `tests/integration/usecase/` - Usecase integration tests

**Property Tests:**

- `tests/property/` - All property-based tests need mock updates

**Performance Tests:**

- `tests/performance/` - Performance tests need singleton setup

### 4. **Test Fixture Refactoring**

All test fixtures in `tests/fixtures/` need to be updated:

```python
# Current fixture pattern
@pytest.fixture
def email_verification_usecase(db_session):
    return EmailVerificationUsecase(db_session)

# New fixture pattern
@pytest.fixture
def email_verification_usecase(
    mock_email_verification_repo,
    mock_user_repo,
    mock_refresh_token_repo,
    mock_email_service,
    mock_jwt_utils,
    mock_config_service,
    mock_audit
):
    return EmailVerificationUsecase(
        mock_email_verification_repo,
        mock_user_repo,
        mock_refresh_token_repo,
        mock_email_service,
        mock_jwt_utils,
        mock_config_service,
        mock_audit
    )
```

### 5. **Mock Strategy**

- **Repository Tests**: Mock DatabaseService and Audit
- **Usecase Tests**: Mock all injected repositories and services
- **Endpoint Tests**: Mock all injected usecases
- **Integration Tests**: Use real DIContainer with test database

### 6. **Test Execution**

- Run existing tests to ensure no functionality is broken
- Add new tests for dependency injection scenarios
- Verify thread safety for shared instances
- Test the complete application with the new architecture

## Updated API Endpoint Structure

With the new dependency injection approach, API endpoints will be refactored to use the dependency injection container:

```python
# Updated email_verification.py example
class EmailVerification:
    ep = APIRouter(prefix="/auth", tags=["auth"])
    __email_verification_uc: EmailVerificationUsecase

    def __init__(self, email_verification_usecase: EmailVerificationUsecase):
        EmailVerification.__email_verification_uc = email_verification_usecase

    @staticmethod
    @ep.post("/verify-email", response_model=TokenResponse)
    async def verify_email(payload: EmailVerificationVerify, request: Request):
        with Context(request) as ctx:
            return await EmailVerification.__email_verification_uc.verify_email(ctx, payload.token)

    @staticmethod
    @ep.post(
        "/resend-verification",
        status_code=status.HTTP_204_NO_CONTENT,
        response_class=Response,
        response_model=None,
    )
    async def resend_verification_email(
        payload: EmailVerificationRequest,
        background_tasks: BackgroundTasks,
        request: Request,
    ) -> Response:
        with Context(request) as ctx:
            await EmailVerification.__email_verification_uc.resend_verification(
                ctx, payload.email, background_tasks, verify_rate_limiter
            )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
```

## Complete Refactoring Scope

This refactoring will affect **ALL** the following components:

### All Usecases (8 total):

1. `EmailVerificationUsecase` - Email verification and resend functionality
2. `WalletUsecase` - Wallet management and portfolio operations
3. `OAuthUsecase` - OAuth authentication flows
4. `TokenPriceUsecase` - Token price management
5. `TokenUsecase` - Token operations
6. `HistoricalBalanceUsecase` - Historical balance tracking
7. `TokenBalanceUsecase` - Token balance operations
8. `PortfolioSnapshotUsecase` - Portfolio snapshot management

### All Repositories (12 total):

1. `UserRepository` - User CRUD operations
2. `EmailVerificationRepository` - Email verification token management
3. `OAuthAccountRepository` - OAuth account management
4. `PasswordResetRepository` - Password reset token management
5. `RefreshTokenRepository` - JWT refresh token management
6. `WalletRepository` - Wallet CRUD operations
7. `PortfolioSnapshotRepository` - Portfolio snapshot management
8. `HistoricalBalanceRepository` - Historical balance tracking
9. `TokenRepository` - Token management
10. `TokenPriceRepository` - Token price data
11. `TokenBalanceRepository` - Token balance operations
12. `AggregateMetricsRepository` - Aggregate metrics (if exists)

### All API Endpoints:

All endpoints in `app/api/endpoints/` will be refactored to use the class-based approach with dependency injection.

### All Tests:

All existing tests need to be refactored to work with the new singleton dependency injection pattern:

**Unit Tests (estimated 200+ tests):**

- `tests/unit/repositories/` - 14 test files for repository tests
- `tests/unit/usecase/` - 9 test files for usecase tests
- `tests/unit/api/` - 4 test files for endpoint tests
- `tests/unit/core/` - 6 test files for core service tests
- `tests/unit/auth/` - 17 test files for authentication tests
- `tests/unit/backups/` - 9 test files for backup tests
- And many more unit test files

**Integration Tests (estimated 100+ tests):**

- `tests/integration/api/` - 14 test files for API endpoint integration tests
- `tests/integration/repositories/` - Repository integration tests
- `tests/integration/usecase/` - Usecase integration tests
- `tests/integration/auth/` - 8 test files for authentication integration tests

**Other Test Categories:**

- `tests/property/` - Property-based tests
- `tests/performance/` - Performance tests
- `tests/fixtures/` - Test fixture files
- `tests/e2e/` - End-to-end tests

## First Actionable Steps

1. Create the `DatabaseService` class in `app/core/database.py` and remove old module-level implementations
2. Create the `ConfigurationService` class in `app/core/config.py`
3. Use the existing `Audit` logging service from `app.utils.logging`
4. Implement the `DIContainer` class in `app/di.py`
5. **Refactor ALL 12 repositories** to use explicit dependency injection (one by one)
6. **Refactor ALL 8 usecases** to use explicit dependency injection (one by one)
7. **Refactor ALL API endpoints** to use the class-based approach (one by one)
8. Update the `DIContainer` to properly initialize and wire all dependencies for ALL components
9. **Refactor ALL existing tests** to use the new singleton dependency injection pattern
   - Update ALL unit tests (200+ tests) to properly mock injected dependencies
   - Update ALL integration tests (100+ tests) to use DIContainer
   - Update ALL test fixtures to create mock singleton instances
   - Update ALL property and performance tests
10. Write comprehensive unit tests for ALL refactored components
11. Run integration tests to ensure the entire system works with the new architecture
