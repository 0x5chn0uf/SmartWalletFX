"""
Enhanced Mock Strategy for Better Test Isolation.

This module provides sophisticated mocking capabilities:
1. Realistic mock behaviors that mirror production services
2. Stateful mocks for integration-like testing
3. Failure scenario simulation
4. Performance characteristic simulation
5. Mock behavior verification and assertions
"""

import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import pytest

from app.domain.schemas.user import UserCreate
from app.models.user import User


class MockUser:
    """A mock User class that behaves like the SQLAlchemy model
    but allows attribute assignment."""

    def __init__(self, **kwargs):
        # Set attributes in the same way SQLAlchemy would
        for attr_name in [
            "id",
            "username",
            "email",
            "hashed_password",
            "email_verified",
            "roles",
            "attributes",
            "profile_picture_url",
            "first_name",
            "last_name",
            "bio",
            "timezone",
            "preferred_currency",
            "notification_preferences",
            "created_at",
            "updated_at",
        ]:
            # Use setattr to mimic SQLAlchemy behavior
            if attr_name in kwargs:
                setattr(self, attr_name, kwargs[attr_name])
            elif attr_name == "email_verified":
                setattr(self, attr_name, False)
            elif attr_name == "roles":
                setattr(self, attr_name, ["individual_investor"])
            elif attr_name == "attributes":
                setattr(self, attr_name, {})
            elif attr_name == "preferred_currency":
                setattr(self, attr_name, "USD")
            else:
                setattr(self, attr_name, None)

        # Create a proper __dict__ for Pydantic compatibility
        self.__dict__.update(
            {
                "id": self.id,
                "username": self.username,
                "email": self.email,
                "hashed_password": self.hashed_password,
                "email_verified": self.email_verified,
                "roles": self.roles,
                "attributes": self.attributes,
                "profile_picture_url": self.profile_picture_url,
                "first_name": self.first_name,
                "last_name": self.last_name,
                "bio": self.bio,
                "timezone": self.timezone,
                "preferred_currency": self.preferred_currency,
                "notification_preferences": self.notification_preferences,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
            }
        )

    def __repr__(self):
        return f"<User username={self.username} email={self.email} roles={self.roles}>"


class MockBehavior(Enum):
    """Defines different mock behavior patterns."""

    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    SLOW_RESPONSE = "slow_response"


@dataclass
class MockCall:
    """Records a mock function call for verification."""

    function_name: str
    args: tuple
    kwargs: dict
    timestamp: datetime
    result: Any
    exception: Optional[Exception] = None


class StatefulMock:
    """Base class for stateful mocks that maintain internal state."""

    def __init__(self):
        self.calls: List[MockCall] = []
        self.state: Dict[str, Any] = {}
        self.behavior = MockBehavior.SUCCESS

    def record_call(
        self,
        func_name: str,
        args: tuple,
        kwargs: dict,
        result: Any,
        exception: Exception = None,
    ):
        """Record a function call for later verification."""
        call = MockCall(
            function_name=func_name,
            args=args,
            kwargs=kwargs,
            timestamp=datetime.utcnow(),
            result=result,
            exception=exception,
        )
        self.calls.append(call)

    def get_calls(self, func_name: Optional[str] = None) -> List[MockCall]:
        """Get recorded calls, optionally filtered by function name."""
        if func_name:
            return [call for call in self.calls if call.function_name == func_name]
        return self.calls

    def clear_calls(self):
        """Clear call history."""
        self.calls.clear()

    def set_behavior(self, behavior: MockBehavior):
        """Set the mock behavior pattern."""
        self.behavior = behavior


