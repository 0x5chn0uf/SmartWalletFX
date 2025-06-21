"""Unit tests for Slack alerting functionality."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.utils.alerting import (
    AlertRateLimiter,
    AlertSeverity,
    SlackAlertingService,
    configure_alerting_service,
    get_alerting_service,
    send_alert,
)


class TestAlertSeverity:
    """Test AlertSeverity enum."""

    def test_alert_severity_values(self):
        """Test AlertSeverity enum values."""
        assert AlertSeverity.INFO.value == "info"
        assert AlertSeverity.WARNING.value == "warning"
        assert AlertSeverity.ERROR.value == "error"
        assert AlertSeverity.CRITICAL.value == "critical"


class TestAlertRateLimiter:
    """Test AlertRateLimiter functionality."""

    @pytest.mark.asyncio
    async def test_rate_limiter_initial_state(self):
        """Test rate limiter initial state."""
        limiter = AlertRateLimiter(max_alerts_per_hour=5)
        assert await limiter.can_send_alert() is True

    @pytest.mark.asyncio
    async def test_rate_limiter_respects_limit(self):
        """Test rate limiter respects the maximum alerts per hour."""
        limiter = AlertRateLimiter(max_alerts_per_hour=2)

        # First two alerts should be allowed
        assert await limiter.can_send_alert() is True
        assert await limiter.can_send_alert() is True

        # Third alert should be rate limited
        assert await limiter.can_send_alert() is False

    @pytest.mark.asyncio
    async def test_rate_limiter_cleanup_old_timestamps(self):
        """Test rate limiter cleans up old timestamps."""
        limiter = AlertRateLimiter(max_alerts_per_hour=1)

        # Add an old timestamp (more than 1 hour ago)
        limiter.alert_timestamps = [0.0]  # Unix epoch start

        # Should be able to send alert (old timestamp cleaned up)
        assert await limiter.can_send_alert() is True
        assert len(limiter.alert_timestamps) == 1


class TestSlackAlertingService:
    """Test SlackAlertingService functionality."""

    def test_service_initialization(self):
        """Test service initialization."""
        service = SlackAlertingService(
            webhook_url="https://hooks.slack.com/test",
            max_alerts_per_hour=5,
            timeout_seconds=15,
        )
        assert service.webhook_url == "https://hooks.slack.com/test"
        assert service.timeout_seconds == 15
        assert service.rate_limiter.max_alerts_per_hour == 5

    def test_get_severity_color(self):
        """Test severity color mapping."""
        service = SlackAlertingService()

        assert service._get_severity_color(AlertSeverity.INFO) == "#36a64f"
        assert service._get_severity_color(AlertSeverity.WARNING) == "#ffa500"
        assert service._get_severity_color(AlertSeverity.ERROR) == "#ff0000"
        assert service._get_severity_color(AlertSeverity.CRITICAL) == "#8b0000"

    def test_build_slack_payload(self):
        """Test Slack payload building."""
        service = SlackAlertingService()
        context = {"error_code": "AUTH_FAILED", "retry_count": 3}

        payload = service._build_slack_payload(
            "JWT rotation failed",
            AlertSeverity.ERROR,
            context,
        )

        assert "attachments" in payload
        assert len(payload["attachments"]) == 1

        attachment = payload["attachments"][0]
        assert attachment["title"] == "JWT Key Rotation Alert - ERROR"
        assert attachment["text"] == "JWT rotation failed"
        assert attachment["color"] == "#ff0000"
        assert len(attachment["fields"]) == 2

    @pytest.mark.asyncio
    async def test_send_alert_without_webhook(self):
        """Test sending alert without webhook URL."""
        service = SlackAlertingService(webhook_url=None)
        result = await service.send_alert("Test message")
        assert result is False

    @pytest.mark.asyncio
    async def test_send_alert_rate_limited(self):
        """Test sending alert when rate limited."""
        service = SlackAlertingService(max_alerts_per_hour=0)  # No alerts allowed
        result = await service.send_alert("Test message")
        assert result is False

    @pytest.mark.asyncio
    async def test_send_alert_success(self):
        """Test successful alert sending."""
        service = SlackAlertingService(webhook_url="https://hooks.slack.com/test")

        # Mock the HTTP session and response
        mock_response = AsyncMock()
        mock_response.status = 200

        mock_session = AsyncMock()
        mock_session.post = AsyncMock(return_value=mock_response)

        with patch.object(service, "_get_session", return_value=mock_session):
            result = await service.send_alert("Test message", AlertSeverity.ERROR)
            assert result is True

    @pytest.mark.asyncio
    async def test_send_alert_http_error(self):
        """Test alert sending with HTTP error."""
        service = SlackAlertingService(webhook_url="https://hooks.slack.com/test")

        # Mock the HTTP session and response
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")

        mock_session = AsyncMock()
        mock_session.post = AsyncMock(return_value=mock_response)

        with patch.object(service, "_get_session", return_value=mock_session):
            result = await service.send_alert("Test message")
            assert result is False

    @pytest.mark.asyncio
    async def test_send_alert_timeout(self):
        """Test alert sending with timeout."""
        service = SlackAlertingService(webhook_url="https://hooks.slack.com/test")

        # Mock the HTTP session to raise timeout
        mock_session = AsyncMock()
        mock_session.post.side_effect = asyncio.TimeoutError()

        with patch.object(service, "_get_session", return_value=mock_session):
            result = await service.send_alert("Test message")
            assert result is False

    @pytest.mark.asyncio
    async def test_close_session(self):
        """Test closing the HTTP session."""
        service = SlackAlertingService()

        # Mock session with closed property
        mock_session = AsyncMock()
        mock_session.closed = False  # Mock the closed property
        mock_session.close = AsyncMock()
        service._session = mock_session

        await service.close()
        mock_session.close.assert_awaited_once()


class TestGlobalAlertingFunctions:
    """Test global alerting functions."""

    def test_get_alerting_service_initial_state(self):
        """Test get_alerting_service initial state."""
        # Reset global service
        import app.utils.alerting as alerting_module

        alerting_module._alerting_service = None

        service = get_alerting_service()
        assert service is None

    def test_configure_alerting_service(self):
        """Test configuring the global alerting service."""
        service = configure_alerting_service(
            webhook_url="https://hooks.slack.com/test",
            max_alerts_per_hour=5,
            timeout_seconds=15,
        )

        assert service.webhook_url == "https://hooks.slack.com/test"
        assert service.rate_limiter.max_alerts_per_hour == 5
        assert service.timeout_seconds == 15

        # Verify global service is set
        global_service = get_alerting_service()
        assert global_service is service

    @pytest.mark.asyncio
    async def test_send_alert_without_service(self):
        """Test send_alert without configured service."""
        # Reset global service
        import app.utils.alerting as alerting_module

        alerting_module._alerting_service = None

        result = await send_alert("Test message")
        assert result is False

    @pytest.mark.asyncio
    async def test_send_alert_with_service(self):
        """Test send_alert with configured service."""
        # Configure service
        service = configure_alerting_service(webhook_url="https://hooks.slack.com/test")

        # Mock successful alert sending
        with patch.object(service, "send_alert", return_value=True):
            result = await send_alert("Test message", AlertSeverity.WARNING)
            assert result is True
