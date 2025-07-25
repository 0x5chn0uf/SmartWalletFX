# Enhanced mocks package

from .base import MockUser, MockBehavior, MockCall, StatefulMock
from .user_repository import MockUserRepository
from .email_service import MockEmailService
from .file_upload_service import MockFileUploadService
from .assertions import MockAssertions


class MockServiceFactory:
    """Factory for creating enhanced mocks with specific behaviors."""

    @staticmethod
    def create_user_repository(
        behavior: MockBehavior = MockBehavior.SUCCESS,
    ) -> MockUserRepository:
        mock = MockUserRepository()
        mock.set_behavior(behavior)
        return mock

    @staticmethod
    def create_email_service(
        behavior: MockBehavior = MockBehavior.SUCCESS,
    ) -> MockEmailService:
        mock = MockEmailService()
        mock.set_behavior(behavior)
        return mock

    @staticmethod
    def create_file_upload_service(
        behavior: MockBehavior = MockBehavior.SUCCESS,
    ) -> MockFileUploadService:
        mock = MockFileUploadService()
        mock.set_behavior(behavior)
        return mock


import pytest


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

