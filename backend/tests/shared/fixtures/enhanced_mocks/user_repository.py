
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Optional

from app.domain.schemas.user import UserCreate
from app.models.user import User

from .base import MockBehavior, MockUser, StatefulMock


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


