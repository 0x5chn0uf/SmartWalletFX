from __future__ import annotations

import importlib
from email.message import EmailMessage
from unittest.mock import Mock, patch

import pytest

import app.services.email_service as es
from app.core.config import settings
from app.services.email_service import (
    EmailService,
    _build_email,
    _send_via_smtp,
)


def test_build_email():
    # Setup
    subject = "Test Subject"
    recipient = "test@example.com"
    body = "Test Body"

    # Execute
    msg = _build_email(subject, recipient, body)

    # Assert
    assert isinstance(msg, EmailMessage)
    assert msg["Subject"] == subject
    assert msg["From"] == settings.EMAIL_FROM
    assert msg["To"] == recipient
    assert msg.get_content().strip() == body


@pytest.mark.asyncio
async def test_send_via_smtp_with_ssl():
    # Setup
    msg = EmailMessage()
    msg["Subject"] = "Test"
    msg["From"] = "from@example.com"
    msg["To"] = "to@example.com"
    msg.set_content("Test content")

    # Mock settings
    with patch("app.services.email_service.settings") as mock_settings, patch(
        "smtplib.SMTP_SSL"
    ) as mock_smtp_ssl, patch("ssl.create_default_context") as mock_ssl_context:
        # Configure settings
        mock_settings.SMTP_HOST = "smtp.example.com"
        mock_settings.SMTP_PORT = 465
        mock_settings.SMTP_USE_SSL = True
        mock_settings.SMTP_USE_TLS = False
        mock_settings.SMTP_USERNAME = "user"
        mock_settings.SMTP_PASSWORD = "pass"

        # Configure mocks
        mock_server = Mock()
        mock_smtp_ssl.return_value = mock_server
        mock_context = Mock()
        mock_ssl_context.return_value = mock_context

        # Execute
        await _send_via_smtp(msg)

        # Assert
        mock_smtp_ssl.assert_called_once_with(
            mock_settings.SMTP_HOST, mock_settings.SMTP_PORT, context=mock_context
        )
        mock_server.login.assert_called_once_with(
            mock_settings.SMTP_USERNAME, mock_settings.SMTP_PASSWORD
        )
        mock_server.send_message.assert_called_once_with(msg)
        mock_server.quit.assert_called_once()


@pytest.mark.asyncio
async def test_send_via_smtp_with_tls():
    # Setup
    msg = EmailMessage()
    msg["Subject"] = "Test"
    msg["From"] = "from@example.com"
    msg["To"] = "to@example.com"
    msg.set_content("Test content")

    # Mock settings
    with patch("app.services.email_service.settings") as mock_settings, patch(
        "smtplib.SMTP"
    ) as mock_smtp, patch("ssl.create_default_context") as mock_ssl_context:
        # Configure settings
        mock_settings.SMTP_HOST = "smtp.example.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USE_SSL = False
        mock_settings.SMTP_USE_TLS = True
        mock_settings.SMTP_USERNAME = "user"
        mock_settings.SMTP_PASSWORD = "pass"

        # Configure mocks
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        mock_context = Mock()
        mock_ssl_context.return_value = mock_context

        # Execute
        await _send_via_smtp(msg)

        # Assert
        mock_smtp.assert_called_once_with(
            mock_settings.SMTP_HOST, mock_settings.SMTP_PORT
        )
        mock_server.starttls.assert_called_once_with(context=mock_context)
        mock_server.login.assert_called_once_with(
            mock_settings.SMTP_USERNAME, mock_settings.SMTP_PASSWORD
        )
        mock_server.send_message.assert_called_once_with(msg)
        mock_server.quit.assert_called_once()


@pytest.mark.asyncio
async def test_send_via_smtp_without_auth():
    # Setup
    msg = EmailMessage()
    msg["Subject"] = "Test"
    msg["From"] = "from@example.com"
    msg["To"] = "to@example.com"
    msg.set_content("Test content")

    # Mock settings
    with patch("app.services.email_service.settings") as mock_settings, patch(
        "smtplib.SMTP"
    ) as mock_smtp:
        # Configure settings
        mock_settings.SMTP_HOST = "smtp.example.com"
        mock_settings.SMTP_PORT = 25
        mock_settings.SMTP_USE_SSL = False
        mock_settings.SMTP_USE_TLS = False
        mock_settings.SMTP_USERNAME = None
        mock_settings.SMTP_PASSWORD = None

        # Configure mocks
        mock_server = Mock()
        mock_smtp.return_value = mock_server

        # Execute
        await _send_via_smtp(msg)

        # Assert
        mock_smtp.assert_called_once_with(
            mock_settings.SMTP_HOST, mock_settings.SMTP_PORT
        )
        mock_server.login.assert_not_called()
        mock_server.send_message.assert_called_once_with(msg)
        mock_server.quit.assert_called_once()


@pytest.mark.asyncio
async def test_send_via_smtp_exception_handling():
    # Setup
    msg = EmailMessage()
    msg["Subject"] = "Test"
    msg["From"] = "from@example.com"
    msg["To"] = "to@example.com"
    msg.set_content("Test content")

    # Mock settings
    with patch("app.services.email_service.settings") as mock_settings, patch(
        "smtplib.SMTP"
    ) as mock_smtp:
        # Configure settings
        mock_settings.SMTP_HOST = "smtp.example.com"
        mock_settings.SMTP_PORT = 25
        mock_settings.SMTP_USE_SSL = False
        mock_settings.SMTP_USE_TLS = False

        # Configure mocks
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        mock_server.send_message.side_effect = Exception("SMTP error")
        mock_server.quit.side_effect = Exception("Quit error")

        # Execute
        with pytest.raises(Exception, match="SMTP error"):
            await _send_via_smtp(msg)

        # Assert
        mock_smtp.assert_called_once()
        mock_server.send_message.assert_called_once()
        mock_server.quit.assert_called_once()


@pytest.mark.asyncio
async def test_send_password_reset():
    # Ensure fresh module state to avoid interference from previous monkeypatches
    importlib.reload(es)
    EmailService = es.EmailService

    # Setup
    email_service = EmailService()
    email = "user@example.com"
    reset_link = "https://example.com/reset/fixed-token"

    # Mock dependencies
    with patch("app.services.email_service._build_email") as mock_build_email, patch(
        "app.services.email_service._send_via_smtp"
    ) as mock_send_via_smtp, patch("app.services.email_service.Audit") as mock_audit:
        mock_msg = Mock(spec=EmailMessage)
        mock_build_email.return_value = mock_msg

        # Execute
        await email_service.send_password_reset(email, reset_link)

        # Assert
        mock_build_email.assert_called_once()
        subject, recipient, body = mock_build_email.call_args[0]
        assert subject == "Reset your SmartWalletFx password"
        assert recipient == email
        assert reset_link in body

        mock_send_via_smtp.assert_awaited_once_with(mock_msg)
        mock_audit.info.assert_called_once_with("send_password_reset", email=email)


@pytest.mark.asyncio
async def test_send_email_verification():
    # Setup
    email_service = EmailService()
    email = "user@example.com"
    verify_link = "https://example.com/verify/token123"

    # Mock dependencies
    with patch("app.services.email_service._build_email") as mock_build_email, patch(
        "app.services.email_service._send_via_smtp"
    ) as mock_send_via_smtp, patch("app.services.email_service.Audit") as mock_audit:
        mock_msg = Mock(spec=EmailMessage)
        mock_build_email.return_value = mock_msg

        # Execute
        await email_service.send_email_verification(email, verify_link)

        # Assert
        mock_build_email.assert_called_once()
        subject, recipient, body = mock_build_email.call_args[0]
        assert subject == "Verify your SmartWalletFx e-mail address"
        assert recipient == email
        assert verify_link in body

        mock_send_via_smtp.assert_awaited_once_with(mock_msg)
        mock_audit.info.assert_called_once_with("send_email_verification", email=email)
