# Service Container Architecture

The backend now uses a lightweight `ServiceContainer` class to manage core dependencies. The container instantiates the `DatabaseService`, `CeleryService`, `SettingsService`, and `LoggingService` and exposes them via properties.

Repositories, use cases and API routers are exposed as singletons. Repository attributes return lazily created instances bound to the container's database service so modules can import them directly while tests can override the container.

```python
from app.core.services import ServiceContainer

container = ServiceContainer()
app = create_app(container)
```

Create and pass a container instance explicitly instead of relying on module-level globals.
