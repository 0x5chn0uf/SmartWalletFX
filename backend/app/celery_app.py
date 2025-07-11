"""Celery application instance relying on :class:`ServiceContainer`."""

from app.core.services import ServiceContainer

container = ServiceContainer()
celery = container.celery.app
