from celery.schedules import crontab

from app.celery_app import celery
from app.core.config import settings


def test_jwt_rotation_beat_schedule_is_configured():
    """
    Tests that the 'jwt-rotation-beat' schedule is correctly configured in Celery.
    """
    assert "jwt-rotation-beat" in celery.conf.beat_schedule
    schedule_config = celery.conf.beat_schedule["jwt-rotation-beat"]
    assert (
        schedule_config["task"] == "app.tasks.jwt_rotation.promote_and_retire_keys_task"
    )

    # Check that the schedule matches the cron expression from settings
    expected_schedule = crontab(*settings.JWT_ROTATION_SCHEDULE_CRON.split())
    assert schedule_config["schedule"] == expected_schedule
