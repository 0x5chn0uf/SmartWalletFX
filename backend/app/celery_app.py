from celery import Celery
from celery.schedules import crontab

celery = Celery(
    "SmartWalletFX",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)
celery.conf.timezone = "UTC"

celery.conf.beat_schedule = {
    # Daily automated database backup (Subtask 8.3)
    "db-backup-daily": {
        "task": "app.tasks.backups.create_backup_task",
        # 02:00 UTC daily – override via settings.BACKUP_SCHEDULE_CRON in future
        "schedule": crontab(hour=2, minute=0),
    },
    "jwt-rotation-beat": {
        "task": "app.tasks.jwt_rotation.promote_and_retire_keys_task",
        "schedule": crontab(minute="*/5"),  # Placeholder, will be replaced
    },
}

import app.tasks.backups  # noqa: F401, E402
import app.tasks.jwt_rotation  # noqa: F401, E402
from app.core.config import settings  # noqa: F401, E402

# Update schedule from settings
celery.conf.beat_schedule["jwt-rotation-beat"]["schedule"] = crontab(
    *settings.JWT_ROTATION_SCHEDULE_CRON.split()
)
