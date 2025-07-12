from __future__ import annotations

import asyncio
import smtplib
import ssl
from email.message import EmailMessage
from typing import Final

from app.core.config import settings
from app.utils.logging import Audit


def _build_email(subject: str, recipient: str, body: str) -> EmailMessage:
    """Return a fully-formed *plain-text* email message."""

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = recipient
    msg.set_content(body)
    return msg


async def _send_via_smtp(message: EmailMessage) -> None:
    """Send *message* using SMTP settings from *settings*.

    This helper runs the blocking smtplib logic in a thread-pool so the
    async API of *EmailService* remains fully asynchronous.
    """

    def _sync_send() -> None:  # executed in a worker thread
        host: Final = settings.SMTP_HOST
        port: Final = settings.SMTP_PORT

        if settings.SMTP_USE_SSL:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(host, port, context=context)
        else:
            server = smtplib.SMTP(host, port)

        try:
            if settings.SMTP_USE_TLS and not settings.SMTP_USE_SSL:
                server.starttls(context=ssl.create_default_context())

            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)

            server.send_message(message)
        finally:
            try:
                server.quit()
            except Exception:  # pragma: no cover – best-effort cleanup
                pass

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _sync_send)


class EmailService:
    """Simplified email service that logs reset links."""

    async def send_password_reset(
        self, email: str, reset_link: str
    ) -> None:  # noqa: D401
        """Send password-reset e-mail and log the event."""

        subject = "Reset your SmartWalletFx password"
        body = (
            "Hello,\n\n"
            "We received a request to reset your SmartWalletFx password. "
            f"You can reset it by clicking the link below:\n\n{reset_link}\n\n"
            "If you did not request a password reset, please ignore this email.\n\n"
            "Regards,\nSmartWalletFx Team"
        )

        msg = _build_email(subject, email, body)
        await _send_via_smtp(msg)
        Audit.info("send_password_reset", email=email)

    async def send_email_verification(
        self, email: str, verify_link: str
    ) -> None:  # noqa: D401
        """Send account-verification e-mail and log the event."""

        subject = "Verify your SmartWalletFx e-mail address"
        body = (
            "Welcome to SmartWalletFx!\n\n"
            "Please verify your e-mail address by clicking the link below:\n\n"
            f"{verify_link}\n\n"
            "If you did not create an account, please ignore this email.\n\n"
            "Regards,\nSmartWalletFx Team"
        )

        msg = _build_email(subject, email, body)
        await _send_via_smtp(msg)
        Audit.info("send_email_verification", email=email)
