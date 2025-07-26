"""Unit tests for EmailService."""

import asyncio
import smtplib
import ssl
from email.message import EmailMessage
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.services.email_service import (
    EmailService,
    _build_email,
    _send_via_smtp,
)


@pytest.fixture
def restore_email_service_methods():
    """Restore original EmailService methods that are patched in conftest.py."""
    import importlib

    import app.services.email_service
    from app.services.email_service import EmailService

    # Store original patched methods
    original_password_reset = EmailService.send_password_reset
    original_email_verification = EmailService.send_email_verification

    # Reload the module to get the original implementations
    importlib.reload(app.services.email_service)
    from app.services.email_service import EmailService as OriginalEmailService

    # Temporarily restore original implementations
    EmailService.send_password_reset = OriginalEmailService.send_password_reset
    EmailService.send_email_verification = OriginalEmailService.send_email_verification

    yield

    # Restore the patched methods
    EmailService.send_password_reset = original_password_reset
    EmailService.send_email_verification = original_email_verification


class TestEmailServiceHelpers:
    """Test helper functions for EmailService."""

    @pytest.mark.unit
    def test_build_email_basic(self):
        """Test building a basic email message."""
        subject = "Test Subject"
        recipient = "test@example.com"
        body = "Test body content"
        email_from = "sender@example.com"

        message = _build_email(subject, recipient, body, email_from)

        assert isinstance(message, EmailMessage)
        assert message["Subject"] == subject
        assert message["From"] == email_from
        assert message["To"] == recipient
        assert message.get_content().strip() == body

    @pytest.mark.unit
    def test_build_email_with_special_characters(self):
        """Test building email with special characters."""
        subject = "Test Subject with ümlaut"
        recipient = "test+tag@example.com"
        body = "Test body with special chars: é, ñ, ü"
        email_from = "sender@example.com"

        message = _build_email(subject, recipient, body, email_from)

        assert message["Subject"] == subject
        assert message["From"] == email_from
        assert message["To"] == recipient
        assert message.get_content().strip() == body

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_send_via_smtp_ssl_with_auth(self):
        """Test SMTP sending with SSL and authentication."""
        # Create a mock email message
        message = EmailMessage()
        message["Subject"] = "Test"
        message["From"] = "sender@example.com"
        message["To"] = "recipient@example.com"
        message.set_content("Test body")

        # Mock configuration
        mock_config = Mock()
        mock_config.SMTP_HOST = "smtp.example.com"
        mock_config.SMTP_PORT = 465
        mock_config.SMTP_USE_SSL = True
        mock_config.SMTP_USE_TLS = False
        mock_config.SMTP_USERNAME = "user@example.com"
        mock_config.SMTP_PASSWORD = "password"

        # Mock SMTP server
        mock_server = Mock()
        mock_server.login = Mock()
        mock_server.send_message = Mock()
        mock_server.quit = Mock()

        with patch(
            "app.services.email_service.smtplib.SMTP_SSL"
        ) as mock_smtp_ssl, patch(
            "app.services.email_service.ssl.create_default_context"
        ) as mock_ssl_context:
            mock_smtp_ssl.return_value = mock_server
            mock_ssl_context.return_value = Mock()

            # Execute
            await _send_via_smtp(message, mock_config)

            # Verify
            mock_smtp_ssl.assert_called_once_with(
                mock_config.SMTP_HOST,
                mock_config.SMTP_PORT,
                context=mock_ssl_context.return_value,
            )
            mock_server.login.assert_called_once_with(
                mock_config.SMTP_USERNAME, mock_config.SMTP_PASSWORD
            )
            mock_server.send_message.assert_called_once_with(message)
            mock_server.quit.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_send_via_smtp_tls_no_auth(self):
        """Test SMTP sending with TLS and no authentication."""
        # Create a mock email message
        message = EmailMessage()
        message["Subject"] = "Test"
        message["From"] = "sender@example.com"
        message["To"] = "recipient@example.com"
        message.set_content("Test body")

        # Mock configuration
        mock_config = Mock()
        mock_config.SMTP_HOST = "smtp.example.com"
        mock_config.SMTP_PORT = 587
        mock_config.SMTP_USE_SSL = False
        mock_config.SMTP_USE_TLS = True
        mock_config.SMTP_USERNAME = None
        mock_config.SMTP_PASSWORD = None

        # Mock SMTP server
        mock_server = Mock()
        mock_server.starttls = Mock()
        mock_server.login = Mock()
        mock_server.send_message = Mock()
        mock_server.quit = Mock()

        with patch("app.services.email_service.smtplib.SMTP") as mock_smtp, patch(
            "app.services.email_service.ssl.create_default_context"
        ) as mock_ssl_context:
            mock_smtp.return_value = mock_server
            mock_ssl_context.return_value = Mock()

            # Execute
            await _send_via_smtp(message, mock_config)

            # Verify
            mock_smtp.assert_called_once_with(
                mock_config.SMTP_HOST, mock_config.SMTP_PORT
            )
            mock_server.starttls.assert_called_once_with(
                context=mock_ssl_context.return_value
            )
            mock_server.login.assert_not_called()  # No auth credentials
            mock_server.send_message.assert_called_once_with(message)
            mock_server.quit.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_send_via_smtp_plain_with_auth(self):
        """Test SMTP sending with plain connection and authentication."""
        # Create a mock email message
        message = EmailMessage()
        message["Subject"] = "Test"
        message["From"] = "sender@example.com"
        message["To"] = "recipient@example.com"
        message.set_content("Test body")

        # Mock configuration
        mock_config = Mock()
        mock_config.SMTP_HOST = "smtp.example.com"
        mock_config.SMTP_PORT = 25
        mock_config.SMTP_USE_SSL = False
        mock_config.SMTP_USE_TLS = False
        mock_config.SMTP_USERNAME = "user@example.com"
        mock_config.SMTP_PASSWORD = "password"

        # Mock SMTP server
        mock_server = Mock()
        mock_server.starttls = Mock()
        mock_server.login = Mock()
        mock_server.send_message = Mock()
        mock_server.quit = Mock()

        with patch("app.services.email_service.smtplib.SMTP") as mock_smtp:
            mock_smtp.return_value = mock_server

            # Execute
            await _send_via_smtp(message, mock_config)

            # Verify
            mock_smtp.assert_called_once_with(
                mock_config.SMTP_HOST, mock_config.SMTP_PORT
            )
            mock_server.starttls.assert_not_called()  # No TLS
            mock_server.login.assert_called_once_with(
                mock_config.SMTP_USERNAME, mock_config.SMTP_PASSWORD
            )
            mock_server.send_message.assert_called_once_with(message)
            mock_server.quit.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_send_via_smtp_quit_exception(self):
        """Test SMTP sending when quit() raises exception."""
        # Create a mock email message
        message = EmailMessage()
        message["Subject"] = "Test"
        message["From"] = "sender@example.com"
        message["To"] = "recipient@example.com"
        message.set_content("Test body")

        # Mock configuration
        mock_config = Mock()
        mock_config.SMTP_HOST = "smtp.example.com"
        mock_config.SMTP_PORT = 25
        mock_config.SMTP_USE_SSL = False
        mock_config.SMTP_USE_TLS = False
        mock_config.SMTP_USERNAME = None
        mock_config.SMTP_PASSWORD = None

        # Mock SMTP server
        mock_server = Mock()
        mock_server.send_message = Mock()
        mock_server.quit = Mock(side_effect=Exception("Connection already closed"))

        with patch("app.services.email_service.smtplib.SMTP") as mock_smtp:
            mock_smtp.return_value = mock_server

            # Execute - should not raise exception
            await _send_via_smtp(message, mock_config)

            # Verify
            mock_server.send_message.assert_called_once_with(message)
            mock_server.quit.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_send_via_smtp_send_exception(self):
        """Test SMTP sending when send_message raises exception."""
        # Create a mock email message
        message = EmailMessage()
        message["Subject"] = "Test"
        message["From"] = "sender@example.com"
        message["To"] = "recipient@example.com"
        message.set_content("Test body")

        # Mock configuration
        mock_config = Mock()
        mock_config.SMTP_HOST = "smtp.example.com"
        mock_config.SMTP_PORT = 25
        mock_config.SMTP_USE_SSL = False
        mock_config.SMTP_USE_TLS = False
        mock_config.SMTP_USERNAME = None
        mock_config.SMTP_PASSWORD = None

        # Mock SMTP server
        mock_server = Mock()
        mock_server.send_message = Mock(
            side_effect=smtplib.SMTPException("Send failed")
        )
        mock_server.quit = Mock()

        with patch("app.services.email_service.smtplib.SMTP") as mock_smtp:
            mock_smtp.return_value = mock_server

            # Execute - should raise exception
            with pytest.raises(smtplib.SMTPException, match="Send failed"):
                await _send_via_smtp(message, mock_config)

            # Verify quit was still called
            mock_server.quit.assert_called_once()


class TestEmailService:
    """Test EmailService class."""

    @pytest.mark.unit
    def test_init(self, mock_config, mock_audit):
        """Test EmailService initialization."""
        service = EmailService(mock_config, mock_audit)

        assert service._EmailService__config_service is mock_config
        assert service._EmailService__audit is mock_audit

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_send_password_reset_success(
        self, email_service_with_di, restore_email_service_methods
    ):
        """Test successful password reset email sending."""
        email = "test@example.com"
        reset_link = "https://example.com/reset?token=abc123"

        # Mock the email service dependencies
        config = email_service_with_di._EmailService__config_service
        config.EMAIL_FROM = "noreply@example.com"
        config.SMTP_HOST = "smtp.example.com"
        config.SMTP_PORT = 587
        config.SMTP_USE_SSL = False
        config.SMTP_USE_TLS = True
        config.SMTP_USERNAME = "user@example.com"
        config.SMTP_PASSWORD = "password"

        with patch(
            "app.services.email_service._send_via_smtp", new_callable=AsyncMock
        ) as mock_send_smtp:
            # Execute
            await email_service_with_di.send_password_reset(email, reset_link)

            # Verify
            mock_send_smtp.assert_awaited_once()
            args, kwargs = mock_send_smtp.call_args
            message = args[0]

            assert isinstance(message, EmailMessage)
            assert message["Subject"] == "Reset your SmartWalletFx password"
            assert message["From"] == "noreply@example.com"
            assert message["To"] == email
            assert reset_link in message.get_content()

            # Verify audit logging
            email_service_with_di._EmailService__audit.info.assert_called_once_with(
                "send_password_reset", email=email
            )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_send_password_reset_smtp_failure(
        self, email_service_with_di, restore_email_service_methods
    ):
        """Test password reset email sending with SMTP failure."""
        email = "test@example.com"
        reset_link = "https://example.com/reset?token=abc123"

        # Mock the email service dependencies
        config = email_service_with_di._EmailService__config_service
        config.EMAIL_FROM = "noreply@example.com"
        config.SMTP_HOST = "smtp.example.com"
        config.SMTP_PORT = 587
        config.SMTP_USE_SSL = False
        config.SMTP_USE_TLS = True
        config.SMTP_USERNAME = "user@example.com"
        config.SMTP_PASSWORD = "password"

        with patch("app.services.email_service._send_via_smtp") as mock_send_smtp:
            mock_send_smtp.side_effect = smtplib.SMTPException("SMTP server error")

            # Execute and verify exception is raised
            with pytest.raises(smtplib.SMTPException, match="SMTP server error"):
                await email_service_with_di.send_password_reset(email, reset_link)

            # Verify audit logging was not called due to exception
            email_service_with_di._EmailService__audit.info.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_send_email_verification_success(
        self, email_service_with_di, restore_email_service_methods
    ):
        """Test successful email verification email sending."""
        email = "test@example.com"
        verify_link = "https://example.com/verify?token=def456"

        # Mock the email service dependencies
        config = email_service_with_di._EmailService__config_service
        config.EMAIL_FROM = "noreply@example.com"
        config.SMTP_HOST = "smtp.example.com"
        config.SMTP_PORT = 587
        config.SMTP_USE_SSL = False
        config.SMTP_USE_TLS = True
        config.SMTP_USERNAME = "user@example.com"
        config.SMTP_PASSWORD = "password"

        with patch(
            "app.services.email_service._send_via_smtp", new_callable=AsyncMock
        ) as mock_send_smtp:
            # Execute
            await email_service_with_di.send_email_verification(email, verify_link)

            # Verify
            mock_send_smtp.assert_awaited_once()
            args, kwargs = mock_send_smtp.call_args
            message = args[0]

            assert isinstance(message, EmailMessage)
            assert message["Subject"] == "Verify your SmartWalletFx e-mail address"
            assert message["From"] == "noreply@example.com"
            assert message["To"] == email
            assert verify_link in message.get_content()

            # Verify audit logging
            email_service_with_di._EmailService__audit.info.assert_called_once_with(
                "send_email_verification", email=email
            )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_send_email_verification_smtp_failure(
        self, email_service_with_di, restore_email_service_methods
    ):
        """Test email verification email sending with SMTP failure."""
        email = "test@example.com"
        verify_link = "https://example.com/verify?token=def456"

        # Mock the email service dependencies
        config = email_service_with_di._EmailService__config_service
        config.EMAIL_FROM = "noreply@example.com"
        config.SMTP_HOST = "smtp.example.com"
        config.SMTP_PORT = 587
        config.SMTP_USE_SSL = False
        config.SMTP_USE_TLS = True
        config.SMTP_USERNAME = "user@example.com"
        config.SMTP_PASSWORD = "password"

        with patch("app.services.email_service._send_via_smtp") as mock_send_smtp:
            mock_send_smtp.side_effect = smtplib.SMTPException("SMTP server error")

            # Execute and verify exception is raised
            with pytest.raises(smtplib.SMTPException, match="SMTP server error"):
                await email_service_with_di.send_email_verification(email, verify_link)

            # Verify audit logging was not called due to exception
            email_service_with_di._EmailService__audit.info.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_send_password_reset_content_format(
        self, email_service_with_di, restore_email_service_methods
    ):
        """Test password reset email content format."""
        email = "user@example.com"
        reset_link = "https://example.com/reset?token=xyz789"

        # Mock the email service dependencies
        config = email_service_with_di._EmailService__config_service
        config.EMAIL_FROM = "noreply@example.com"
        config.SMTP_HOST = "smtp.example.com"
        config.SMTP_PORT = 587
        config.SMTP_USE_SSL = False
        config.SMTP_USE_TLS = True
        config.SMTP_USERNAME = "user@example.com"
        config.SMTP_PASSWORD = "password"

        with patch(
            "app.services.email_service._send_via_smtp", new_callable=AsyncMock
        ) as mock_send_smtp:
            # Execute
            await email_service_with_di.send_password_reset(email, reset_link)

            # Verify content format
            args, kwargs = mock_send_smtp.call_args
            message = args[0]
            body = message.get_content()

            assert "Hello," in body
            assert "SmartWalletFx password" in body
            assert reset_link in body
            assert "If you did not request a password reset" in body
            assert "SmartWalletFx Team" in body

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_send_email_verification_content_format(
        self, email_service_with_di, restore_email_service_methods
    ):
        """Test email verification email content format."""
        email = "user@example.com"
        verify_link = "https://example.com/verify?token=xyz789"

        # Mock the email service dependencies
        config = email_service_with_di._EmailService__config_service
        config.EMAIL_FROM = "noreply@example.com"
        config.SMTP_HOST = "smtp.example.com"
        config.SMTP_PORT = 587
        config.SMTP_USE_SSL = False
        config.SMTP_USE_TLS = True
        config.SMTP_USERNAME = "user@example.com"
        config.SMTP_PASSWORD = "password"

        with patch(
            "app.services.email_service._send_via_smtp", new_callable=AsyncMock
        ) as mock_send_smtp:
            # Execute
            await email_service_with_di.send_email_verification(email, verify_link)

            # Verify content format
            args, kwargs = mock_send_smtp.call_args
            message = args[0]
            body = message.get_content()

            assert "Welcome to SmartWalletFx!" in body
            assert "verify your e-mail address" in body
            assert verify_link in body
            assert "If you did not create an account" in body
            assert "SmartWalletFx Team" in body
