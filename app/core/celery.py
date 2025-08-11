"""Celery service for background task processing."""

from celery import Celery
from celery.schedules import crontab

from app.core.config import Configuration


class CoreCelery:
    """Celery service for managing background tasks and scheduling."""

    def __init__(self, config: Configuration):
        """Initialize Celery service with configuration."""
        self.config = config
        self._celery_app = None
        self._setup_celery()

    def _setup_celery(self):
        """Set up Celery application with configuration."""
        self._celery_app = Celery(
            self.config.PROJECT_NAME,
            broker=self.config.REDIS_URL,
            backend=self.config.REDIS_URL,
        )
        self._celery_app.conf.timezone = "UTC"
        self._setup_beat_schedule()

    def _setup_beat_schedule(self):
        """Set up Celery beat schedule for periodic tasks."""
        self._celery_app.conf.beat_schedule = {
            "jwt-rotation-beat": {
                "task": "app.tasks.jwt_rotation.promote_and_retire_keys_task",
                "schedule": crontab(*self.config.JWT_ROTATION_SCHEDULE_CRON.split()),
            }
        }

    @property
    def app(self) -> Celery:
        """Get the Celery application instance."""
        return self._celery_app

    def get_celery_app(self) -> Celery:
        """Get the Celery application instance (alternative method)."""
        return self._celery_app
