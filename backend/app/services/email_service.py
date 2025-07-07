from __future__ import annotations

from app.utils.logging import Audit


class EmailService:
    """Simplified email service that logs reset links."""

    async def send_password_reset(self, email: str, reset_link: str) -> None:
        Audit.info("send_password_reset", email=email, reset_link=reset_link)
