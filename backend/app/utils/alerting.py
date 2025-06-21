"""Slack webhook alerting service for system notifications.

This module provides a configurable Slack webhook service for sending
alerts and notifications, with support for different severity levels
and rate limiting to prevent alert spam.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

import aiohttp

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels for Slack notifications."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertRateLimiter:
    """Rate limiter for alerts to prevent spam."""

    def __init__(self, max_alerts_per_hour: int = 10):
        """Initialize the rate limiter.

        Args:
            max_alerts_per_hour: Maximum number of alerts allowed per hour.
        """
        self.max_alerts_per_hour = max_alerts_per_hour
        self.alert_timestamps: list[float] = []
        self._lock = asyncio.Lock()

    async def can_send_alert(self) -> bool:
        """Check if an alert can be sent based on rate limiting.

        Returns:
            True if an alert can be sent, False if rate limited.
        """
        async with self._lock:
            now = time.time()
            # Remove timestamps older than 1 hour
            self.alert_timestamps = [
                ts for ts in self.alert_timestamps if now - ts < 3600
            ]

            if len(self.alert_timestamps) >= self.max_alerts_per_hour:
                return False

            self.alert_timestamps.append(now)
            return True


class SlackAlertingService:
    """Slack webhook alerting service."""

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        max_alerts_per_hour: int = 10,
        timeout_seconds: int = 10,
    ):
        """Initialize the Slack alerting service.

        Args:
            webhook_url: Slack webhook URL for sending alerts.
            max_alerts_per_hour: Maximum alerts per hour for rate limiting.
            timeout_seconds: HTTP timeout for webhook requests.
        """
        self.webhook_url = webhook_url
        self.timeout_seconds = timeout_seconds
        self.rate_limiter = AlertRateLimiter(max_alerts_per_hour)
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create the HTTP session.

        Returns:
            The aiohttp ClientSession instance.
        """
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    def _get_severity_color(self, severity: AlertSeverity) -> str:
        """Get the color for a severity level.

        Args:
            severity: The alert severity level.

        Returns:
            Hex color code for the severity level.
        """
        colors = {
            AlertSeverity.INFO: "#36a64f",  # Green
            AlertSeverity.WARNING: "#ffa500",  # Orange
            AlertSeverity.ERROR: "#ff0000",  # Red
            AlertSeverity.CRITICAL: "#8b0000",  # Dark red
        }
        return colors.get(severity, "#808080")  # Gray default

    def _build_slack_payload(
        self,
        message: str,
        severity: AlertSeverity,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build the Slack webhook payload.

        Args:
            message: The alert message.
            severity: The alert severity level.
            context: Optional context data to include.

        Returns:
            The Slack webhook payload dictionary.
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # Build attachment
        attachment = {
            "color": self._get_severity_color(severity),
            "title": f"JWT Key Rotation Alert - {severity.value.upper()}",
            "text": message,
            "ts": timestamp,
            "fields": [],
        }

        # Add context fields if provided
        if context:
            for key, value in context.items():
                attachment["fields"].append(
                    {
                        "title": key.replace("_", " ").title(),
                        "value": str(value),
                        "short": True,
                    }
                )

        return {
            "attachments": [attachment],
        }

    async def send_alert(
        self,
        message: str,
        severity: AlertSeverity = AlertSeverity.ERROR,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send an alert via Slack webhook.

        Args:
            message: The alert message to send.
            severity: The alert severity level.
            context: Optional context data to include in the alert.

        Returns:
            True if the alert was sent successfully, False otherwise.
        """
        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured - alert not sent")
            return False

        # Check rate limiting
        if not await self.rate_limiter.can_send_alert():
            logger.warning("Alert rate limit exceeded - alert not sent")
            return False

        try:
            session = await self._get_session()
            payload = self._build_slack_payload(message, severity, context)

            response = await session.post(
                self.webhook_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout_seconds),
            )

            if response.status == 200:
                logger.info("Slack alert sent successfully: %s", message)
                return True
            else:
                logger.error(
                    "Failed to send Slack alert: HTTP %d - %s",
                    response.status,
                    await response.text(),
                )
                return False

        except asyncio.TimeoutError:
            logger.error("Timeout sending Slack alert: %s", message)
            return False
        except Exception as exc:
            logger.exception("Error sending Slack alert: %s", exc)
            return False


# Global alerting service instance
_alerting_service: Optional[SlackAlertingService] = None


def get_alerting_service() -> Optional[SlackAlertingService]:
    """Get the global alerting service instance.

    Returns:
        The SlackAlertingService instance if configured, None otherwise.
    """
    return _alerting_service


def configure_alerting_service(
    webhook_url: Optional[str] = None,
    max_alerts_per_hour: int = 10,
    timeout_seconds: int = 10,
) -> SlackAlertingService:
    """Configure the global alerting service.

    Args:
        webhook_url: Slack webhook URL for sending alerts.
        max_alerts_per_hour: Maximum alerts per hour for rate limiting.
        timeout_seconds: HTTP timeout for webhook requests.

    Returns:
        The configured SlackAlertingService instance.
    """
    global _alerting_service
    _alerting_service = SlackAlertingService(
        webhook_url=webhook_url,
        max_alerts_per_hour=max_alerts_per_hour,
        timeout_seconds=timeout_seconds,
    )
    return _alerting_service


async def send_alert(
    message: str,
    severity: AlertSeverity = AlertSeverity.ERROR,
    context: Optional[Dict[str, Any]] = None,
) -> bool:
    """Send an alert using the global alerting service.

    Args:
        message: The alert message to send.
        severity: The alert severity level.
        context: Optional context data to include in the alert.

    Returns:
        True if the alert was sent successfully, False otherwise.
    """
    service = get_alerting_service()
    if service is None:
        logger.warning("Alerting service not configured - alert not sent")
        return False

    return await service.send_alert(message, severity, context)
