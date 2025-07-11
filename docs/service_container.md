# Service Container Architecture

The backend now uses a lightweight `ServiceContainer` class to manage core dependencies. The container instantiates the `DatabaseService`, `CeleryService`, `SettingsService`, and `LoggingService` and exposes them via properties.

Repositories, use cases and API routers are also exposed as singletons so modules can import them directly while still allowing tests to override the container.

```python
from app.core.services import ServiceContainer

container = ServiceContainer()
app = create_app(container)
```

The default container instance lives in `app.core.database` for backwards compatibility but new code should create its own container instance and pass it explicitly.
