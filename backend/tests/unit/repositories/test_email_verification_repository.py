from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from app.models.email_verification import EmailVerification
from app.repositories.email_verification_repository import (
    EmailVerificationRepository,
)


def setup_mock_session(repository, mock_session):
    """Helper function to set up mock session for repository tests."""

    @asynccontextmanager
    async def mock_get_session():
        yield mock_session

    # Patch the repository's database service get_session method
    repository._EmailVerificationRepository__database.get_session = mock_get_session


@pytest.fixture
def mock_database():
    """Mock CoreDatabase."""
    return Mock()


@pytest.fixture
def mock_audit():
    """Mock Audit service."""
    return Mock()


@pytest.fixture
def email_verification_repository(mock_database, mock_audit):
    """Create EmailVerificationRepository with mocked dependencies."""
    return EmailVerificationRepository(mock_database, mock_audit)


def test_email_verification_repository_constructor_dependencies():
    """Test that EmailVerificationRepository properly accepts dependencies in constructor."""
    # Arrange
    mock_database = Mock()
    mock_audit = Mock()

    # Act
    repository = EmailVerificationRepository(mock_database, mock_audit)

    # Assert
    assert repository._EmailVerificationRepository__database == mock_database
    assert repository._EmailVerificationRepository__audit == mock_audit
