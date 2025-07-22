"""Celery application instance for CLI commands.

This module provides the celery instance for use with Celery CLI commands
(celery worker, celery beat, etc.) by using the CeleryService from DIContainer.
"""

from .main import di_container

celery_service = di_container.get_core("celery")
celery = celery_service.get_celery_app()

import app.tasks.jwt_rotation  # noqa: F401, E402
