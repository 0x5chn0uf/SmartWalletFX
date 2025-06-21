from celery import Celery
from celery.schedules import crontab

celery = Celery(
    "SmartWalletFX",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)
celery.conf.timezone = "UTC"

celery.conf.beat_schedule = {
    "collect-snapshots-every-hours": {
        "task": "app.tasks.snapshots.collect_portfolio_snapshots",
        "schedule": crontab(hour="*", minute="0"),
    },
    # Daily automated database backup (Subtask 8.3)
    "db-backup-daily": {
        "task": "app.tasks.backups.create_backup_task",
        # 02:00 UTC daily – override via settings.BACKUP_SCHEDULE_CRON in future
        "schedule": crontab(hour=2, minute=0),
    },
}

import app.tasks.backups  # noqa: F401, E402
import app.tasks.snapshots  # noqa: F401, E402
