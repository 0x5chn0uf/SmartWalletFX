
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import MockBehavior, StatefulMock


class MockEmailService(StatefulMock):
    """Enhanced mock email service with delivery tracking."""

    def __init__(self):
        super().__init__()
        self.sent_emails: List[Dict[str, Any]] = []

    async def send_verification_email(self, email: str, token: str) -> bool:
        """Mock sending verification email."""
        func_name = "send_verification_email"

        try:
            if self.behavior == MockBehavior.FAILURE:
                self.record_call(func_name, (email, token), {}, False)
                return False
            elif self.behavior == MockBehavior.TIMEOUT:
                await asyncio.sleep(10)

            # Record sent email
            email_record = {
                "type": "verification",
                "to": email,
                "token": token,
                "sent_at": datetime.utcnow(),
                "delivered": True,
            }
            self.sent_emails.append(email_record)

            self.record_call(func_name, (email, token), {}, True)
            return True

        except Exception as e:
            self.record_call(func_name, (email, token), {}, False, e)
            return False

    async def send_password_reset_email(self, email: str, token: str) -> bool:
        """Mock sending password reset email."""
        func_name = "send_password_reset_email"

        try:
            if self.behavior == MockBehavior.FAILURE:
                return False

            email_record = {
                "type": "password_reset",
                "to": email,
                "token": token,
                "sent_at": datetime.utcnow(),
                "delivered": True,
            }
            self.sent_emails.append(email_record)

            self.record_call(func_name, (email, token), {}, True)
            return True

        except Exception as e:
            self.record_call(func_name, (email, token), {}, False, e)
            return False

    def get_sent_emails(self, email_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get sent emails, optionally filtered by type."""
        if email_type:
            return [email for email in self.sent_emails if email["type"] == email_type]
        return self.sent_emails.copy()


