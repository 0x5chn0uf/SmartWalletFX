"""Celery application instance relying on :class:`ServiceContainer`."""

from app.core.services import ServiceContainer


def create_celery(container: ServiceContainer | None = None):
    """Return a Celery app configured from *container*."""

    cont = container or ServiceContainer()
    app = cont.celery.app
    # Expose container for tasks that need access to settings/database
    app.service_container = cont  # type: ignore[attr-defined]
    return app


celery = create_celery()
