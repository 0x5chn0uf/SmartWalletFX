import pytest

from app.celery_app import celery


def test_backup_schedule_registered():
    """Celery beat should include the daily db-backup task entry."""

    schedule = celery.conf.beat_schedule
    assert "db-backup-daily" in schedule, "db-backup-daily schedule missing"
    entry = schedule["db-backup-daily"]
    assert (
        entry["task"] == "app.tasks.backups.create_backup_task"
    ), "Backup task path mismatch"
    # schedule should be a celery crontab set to run daily
    from celery.schedules import crontab

    cron = entry["schedule"]
    assert isinstance(cron, crontab)
