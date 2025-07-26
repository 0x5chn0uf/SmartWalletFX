from __future__ import annotations

from abc import ABC, abstractmethod


class EmailServiceInterface(ABC):
    """Interface for sending application e-mails."""

    @abstractmethod
    async def send_password_reset(self, email: str, reset_link: str) -> None:
        """Send a password reset e-mail."""

    @abstractmethod
    async def send_email_verification(self, email: str, verify_link: str) -> None:
        """Send an account verification e-mail."""
