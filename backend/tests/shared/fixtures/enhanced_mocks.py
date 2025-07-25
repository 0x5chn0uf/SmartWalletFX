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


class MockUserRepository(StatefulMock):
    """Enhanced mock user repository with realistic behaviors."""

    def __init__(self):
        super().__init__()
        self.users: Dict[str, User] = {}
        self.next_id = 1
        self._configured_methods = {}

    def configure_repository_mock(self, entity_type: str, **method_configs):
        """Configure specific mock methods with custom behavior."""
        self._configured_methods.update(method_configs)

        # Apply configurations to the mock
        for method_name, mock_config in method_configs.items():
            setattr(self, method_name, mock_config)

    async def create(self, user_data: UserCreate) -> MockUser:
        """Mock user creation with realistic validation."""
        func_name = "create"

        try:
            # Simulate behavior patterns
            if self.behavior == MockBehavior.FAILURE:
                raise ValueError("Database error")
            elif self.behavior == MockBehavior.TIMEOUT:
                await asyncio.sleep(10)
            elif self.behavior == MockBehavior.SLOW_RESPONSE:
                await asyncio.sleep(0.5)

            # Check for duplicate email/username
            for user in self.users.values():
                if user.email == user_data.email:
                    raise ValueError("Email already exists")
                if user.username == user_data.username:
                    raise ValueError("Username already exists")

            # Create new user
            user_id = uuid.uuid4()
            self.next_id += 1

            user = MockUser(
                id=user_id,
                username=user_data.username,
                email=user_data.email,
                hashed_password="hashed_" + user_data.password,
                email_verified=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            self.users[str(user_id)] = user
            self.record_call(func_name, (user_data,), {}, user)
            return user

        except Exception as e:
            self.record_call(func_name, (user_data,), {}, None, e)
            raise

    async def get_by_id(self, user_id: str) -> Optional[MockUser]:
        """Mock get user by ID."""
        func_name = "get_by_id"

        try:
            if self.behavior == MockBehavior.FAILURE:
                raise ValueError("Database connection error")

            user = self.users.get(user_id)
            self.record_call(func_name, (user_id,), {}, user)
            return user

        except Exception as e:
            self.record_call(func_name, (user_id,), {}, None, e)
            raise

    async def get_by_email(self, email: str) -> Optional[MockUser]:
        """Mock get user by email."""
        func_name = "get_by_email"

        try:
            if self.behavior == MockBehavior.FAILURE:
                raise ValueError("Database connection error")

            user = next((u for u in self.users.values() if u.email == email), None)
            self.record_call(func_name, (email,), {}, user)
            return user

        except Exception as e:
            self.record_call(func_name, (email,), {}, None, e)
            raise

    async def save(self, user: User) -> MockUser:
        """Mock save user (used by auth usecase)."""
        func_name = "save"

        try:
            # Preserve existing user ID if it exists, otherwise create new one
            user_id = getattr(user, "id", None) or uuid.uuid4()
            now = datetime.utcnow()

            # Create a MockUser that can be serialized properly
            saved_user = MockUser(
                id=user_id,
                username=user.username,
                email=user.email,
                hashed_password=user.hashed_password,
                email_verified=getattr(user, "email_verified", False),
                roles=getattr(user, "roles", ["individual_investor"]),
                attributes=getattr(user, "attributes", {}),
                created_at=getattr(user, "created_at", now),
                updated_at=now,
            )

            # Store the user
            self.users[str(user_id)] = saved_user
            self.record_call(func_name, (user,), {}, saved_user)
            return saved_user

        except Exception as e:
            self.record_call(func_name, (user,), {}, None, e)
            raise

    async def get_by_username(self, username: str) -> Optional[MockUser]:
        """Mock get user by username."""
        func_name = "get_by_username"

        try:
            if self.behavior == MockBehavior.FAILURE:
                raise ValueError("Database connection error")

            user = next(
                (u for u in self.users.values() if u.username == username), None
            )
            self.record_call(func_name, (username,), {}, user)
            return user

        except Exception as e:
            self.record_call(func_name, (username,), {}, None, e)
            raise

    async def update(self, user_id: str, user_data: dict) -> Optional[User]:
        """Mock update user."""
        func_name = "update"

        try:
            if self.behavior == MockBehavior.FAILURE:
                raise ValueError("Database update error")

            user = self.users.get(user_id)
            if not user:
                self.record_call(func_name, (user_id, user_data), {}, None)
                return None

            # Update user fields
            for key, value in user_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)

            self.users[user_id] = user
            self.record_call(func_name, (user_id, user_data), {}, user)
            return user

        except Exception as e:
            self.record_call(func_name, (user_id, user_data), {}, None, e)
            raise

    async def delete(self, user_id: str) -> bool:
        """Mock delete user."""
        func_name = "delete"

        try:
            if self.behavior == MockBehavior.FAILURE:
                raise ValueError("Database delete error")

            user = self.users.pop(user_id, None)
            result = user is not None
            self.record_call(func_name, (user_id,), {}, result)
            return result

        except Exception as e:
            self.record_call(func_name, (user_id,), {}, None, e)
            raise


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


class MockFileUploadService(StatefulMock):
    """Enhanced mock file upload service with file tracking."""

    def __init__(self):
        super().__init__()
        self.uploaded_files: Dict[str, Dict[str, Any]] = {}

    async def upload_profile_picture(
        self, user_id: str, file_data: bytes, filename: str
    ) -> str:
        """Mock file upload with realistic behavior."""
        func_name = "upload_profile_picture"

        try:
            if self.behavior == MockBehavior.FAILURE:
                raise ValueError("Upload failed")
            elif self.behavior == MockBehavior.SLOW_RESPONSE:
                await asyncio.sleep(1)  # Simulate slow upload

            # Generate mock file URL
            file_id = str(uuid.uuid4())
            file_url = f"https://storage.example.com/profiles/{file_id}_{filename}"

            # Track uploaded file
            self.uploaded_files[file_url] = {
                "user_id": user_id,
                "filename": filename,
                "size": len(file_data),
                "uploaded_at": datetime.utcnow(),
                "file_id": file_id,
            }

            self.record_call(func_name, (user_id, file_data, filename), {}, file_url)
            return file_url

        except Exception as e:
            self.record_call(func_name, (user_id, file_data, filename), {}, None, e)
            raise

    async def delete_profile_picture(self, file_url: str) -> bool:
        """Mock file deletion."""
        func_name = "delete_profile_picture"

        try:
            if self.behavior == MockBehavior.FAILURE:
                return False

            if file_url in self.uploaded_files:
                del self.uploaded_files[file_url]

            self.record_call(func_name, (file_url,), {}, True)
            return True

        except Exception as e:
            self.record_call(func_name, (file_url,), {}, False, e)
            return False


class MockServiceFactory:
    """Factory for creating enhanced mocks with specific behaviors."""

    @staticmethod
    def create_user_repository(
        behavior: MockBehavior = MockBehavior.SUCCESS,
    ) -> MockUserRepository:
        """Create a mock user repository with specified behavior."""
        mock = MockUserRepository()
        mock.set_behavior(behavior)
        return mock

    @staticmethod
    def create_email_service(
        behavior: MockBehavior = MockBehavior.SUCCESS,
    ) -> MockEmailService:
        """Create a mock email service with specified behavior."""
        mock = MockEmailService()
        mock.set_behavior(behavior)
        return mock

    @staticmethod
    def create_file_upload_service(
        behavior: MockBehavior = MockBehavior.SUCCESS,
    ) -> MockFileUploadService:
        """Create a mock file upload service with specified behavior."""
        mock = MockFileUploadService()
        mock.set_behavior(behavior)
        return mock


# Mock assertion helpers
class MockAssertions:
    """Utilities for asserting mock behaviors."""

    @staticmethod
    def assert_called_once_with(mock: StatefulMock, func_name: str, *args, **kwargs):
        """Assert that a function was called exactly once with specific arguments."""
        calls = mock.get_calls(func_name)
        assert (
            len(calls) == 1
        ), f"Expected {func_name} to be called once, got {len(calls)} calls"

        call = calls[0]
        assert call.args == args, f"Expected args {args}, got {call.args}"
        assert call.kwargs == kwargs, f"Expected kwargs {kwargs}, got {call.kwargs}"

    @staticmethod
    def assert_not_called(mock: StatefulMock, func_name: str):
        """Assert that a function was not called."""
        calls = mock.get_calls(func_name)
        assert (
            len(calls) == 0
        ), f"Expected {func_name} not to be called, got {len(calls)} calls"

    @staticmethod
    def assert_call_count(mock: StatefulMock, func_name: str, expected_count: int):
        """Assert specific call count for a function."""
        calls = mock.get_calls(func_name)
        assert (
            len(calls) == expected_count
        ), f"Expected {expected_count} calls, got {len(calls)}"


# Pytest fixtures for enhanced mocks
@pytest.fixture
def mock_user_repository_enhanced():
    """Provide enhanced mock user repository."""
    return MockServiceFactory.create_user_repository()


@pytest.fixture
def mock_email_service_enhanced():
    """Provide enhanced mock email service."""
    return MockServiceFactory.create_email_service()


@pytest.fixture
def mock_file_upload_service_enhanced():
    """Provide enhanced mock file upload service."""
    return MockServiceFactory.create_file_upload_service()


@pytest.fixture
def mock_service_factory():
    """Provide mock service factory for creating custom mocks."""
    return MockServiceFactory


@pytest.fixture
def mock_assertions():
    """Provide mock assertion utilities."""
    return MockAssertions


# Behavior-specific fixtures
@pytest.fixture
def failing_user_repository():
    """Provide user repository that simulates failures."""
    return MockServiceFactory.create_user_repository(MockBehavior.FAILURE)


@pytest.fixture
def slow_email_service():
    """Provide email service that simulates slow responses."""
    return MockServiceFactory.create_email_service(MockBehavior.SLOW_RESPONSE)


@pytest.fixture
def timeout_file_service():
    """Provide file service that simulates timeouts."""
    return MockServiceFactory.create_file_upload_service(MockBehavior.TIMEOUT)
