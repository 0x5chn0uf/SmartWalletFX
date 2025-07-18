from __future__ import annotations

import hashlib
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy import select

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


# Using shared fixtures from tests.shared.fixtures.core for mock_database and mock_audit


# Using shared fixtures from tests.shared.fixtures.core for mock_session


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


@pytest.mark.asyncio
async def test_create_success(email_verification_repository, mock_session):
    """Test successful creation of email verification token."""
    # Arrange
    setup_mock_session(email_verification_repository, mock_session)
    token = "test_token"
    user_id = uuid.uuid4()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    # Act
    result = await email_verification_repository.create(token, user_id, expires_at)

    # Assert
    assert isinstance(result, EmailVerification)
    assert result.token_hash == hashlib.sha256(token.encode()).hexdigest()
    assert result.user_id == user_id
    assert result.expires_at == expires_at
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()
    email_verification_repository._EmailVerificationRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_create_exception_handling(email_verification_repository, mock_session):
    """Test exception handling in create method."""
    # Arrange
    setup_mock_session(email_verification_repository, mock_session)
    mock_session.commit.side_effect = Exception("Database error")

    token = "test_token"
    user_id = uuid.uuid4()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    # Act & Assert
    with pytest.raises(Exception, match="Database error"):
        await email_verification_repository.create(token, user_id, expires_at)

    email_verification_repository._EmailVerificationRepository__audit.error.assert_called_once()


@pytest.mark.asyncio
async def test_get_valid_found(email_verification_repository, mock_session):
    """Test getting a valid email verification token that exists."""
    # Arrange
    setup_mock_session(email_verification_repository, mock_session)
    token = "test_token"
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    mock_ev = Mock()
    mock_ev.token_hash = token_hash
    mock_ev.user_id = uuid.uuid4()
    mock_ev.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    mock_ev.used = False

    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_ev
    mock_session.execute.return_value = mock_result

    # Act
    result = await email_verification_repository.get_valid(token)

    # Assert
    assert result == mock_ev
    mock_session.execute.assert_called_once()
    email_verification_repository._EmailVerificationRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_get_valid_not_found(email_verification_repository, mock_session):
    """Test getting a valid email verification token that doesn't exist."""
    # Arrange
    setup_mock_session(email_verification_repository, mock_session)
    token = "test_token"

    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Act
    result = await email_verification_repository.get_valid(token)

    # Assert
    assert result is None
    mock_session.execute.assert_called_once()
    email_verification_repository._EmailVerificationRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_get_valid_exception_handling(
    email_verification_repository, mock_session
):
    """Test exception handling in get_valid method."""
    # Arrange
    setup_mock_session(email_verification_repository, mock_session)
    mock_session.execute.side_effect = Exception("Database error")

    token = "test_token"

    # Act & Assert
    with pytest.raises(Exception, match="Database error"):
        await email_verification_repository.get_valid(token)

    email_verification_repository._EmailVerificationRepository__audit.error.assert_called_once()


@pytest.mark.asyncio
async def test_mark_used_success(email_verification_repository, mock_session):
    """Test successful marking of email verification token as used."""
    # Arrange
    setup_mock_session(email_verification_repository, mock_session)

    mock_ev = Mock()
    mock_ev.token_hash = "test_hash"
    mock_ev.used = False

    mock_merged_ev = Mock()
    mock_merged_ev.used = False
    mock_session.merge.return_value = mock_merged_ev

    # Act
    await email_verification_repository.mark_used(mock_ev)

    # Assert
    mock_session.merge.assert_called_once_with(mock_ev)
    assert mock_merged_ev.used is True
    mock_session.commit.assert_called_once()
    email_verification_repository._EmailVerificationRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_mark_used_exception_handling(
    email_verification_repository, mock_session
):
    """Test exception handling in mark_used method."""
    # Arrange
    setup_mock_session(email_verification_repository, mock_session)
    mock_session.merge.side_effect = Exception("Database error")

    mock_ev = Mock()
    mock_ev.token_hash = "test_hash"

    # Act & Assert
    with pytest.raises(Exception, match="Database error"):
        await email_verification_repository.mark_used(mock_ev)

    email_verification_repository._EmailVerificationRepository__audit.error.assert_called_once()


@pytest.mark.asyncio
async def test_delete_expired_success(email_verification_repository, mock_session):
    """Test successful deletion of expired email verification tokens."""
    # Arrange
    setup_mock_session(email_verification_repository, mock_session)

    mock_result = Mock()
    mock_result.rowcount = 5
    mock_session.execute.return_value = mock_result

    # Act
    count = await email_verification_repository.delete_expired()

    # Assert
    assert count == 5
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()
    email_verification_repository._EmailVerificationRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_delete_expired_exception_handling(
    email_verification_repository, mock_session
):
    """Test exception handling in delete_expired method."""
    # Arrange
    setup_mock_session(email_verification_repository, mock_session)
    mock_session.execute.side_effect = Exception("Database error")

    # Act & Assert
    with pytest.raises(Exception, match="Database error"):
        await email_verification_repository.delete_expired()

    email_verification_repository._EmailVerificationRepository__audit.error.assert_called_once()


@pytest.mark.asyncio
async def test_token_hashing_consistency():
    """Test that token hashing is consistent across methods."""
    # Arrange
    token = "test_token"
    expected_hash = hashlib.sha256(token.encode()).hexdigest()

    mock_database = Mock()
    mock_audit = Mock()
    repository = EmailVerificationRepository(mock_database, mock_audit)

    # Mock session for create
    mock_session = Mock()
    mock_session.add = Mock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.execute = AsyncMock()

    setup_mock_session(repository, mock_session)

    user_id = uuid.uuid4()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    # Act
    await repository.create(token, user_id, expires_at)

    # Assert - check that the EmailVerification object was created with correct hash
    call_args = mock_session.add.call_args[0][0]
    assert call_args.token_hash == expected_hash


@pytest.mark.asyncio
async def test_audit_logging_patterns(email_verification_repository, mock_session):
    """Test that audit logging follows consistent patterns."""
    # Arrange
    setup_mock_session(email_verification_repository, mock_session)
    audit_mock = email_verification_repository._EmailVerificationRepository__audit

    # Test create audit logging
    token = "test_token"
    user_id = uuid.uuid4()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    # Act
    await email_verification_repository.create(token, user_id, expires_at)

    # Assert
    audit_calls = audit_mock.info.call_args_list
    assert len(audit_calls) == 2  # started and success
    assert "email_verification_repository_create_started" in str(audit_calls[0])
    assert "email_verification_repository_create_success" in str(audit_calls[1])


@pytest.mark.asyncio
async def test_get_valid_query_structure(email_verification_repository, mock_session):
    """Test that get_valid builds the correct SQL query structure."""
    # Arrange
    setup_mock_session(email_verification_repository, mock_session)
    token = "test_token"

    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Act
    await email_verification_repository.get_valid(token)

    # Assert
    mock_session.execute.assert_called_once()
    call_args = mock_session.execute.call_args[0][0]
    # The query should be a select statement
    assert hasattr(call_args, "whereclause")
    # Should have proper where conditions for token_hash, expires_at, and used
    where_clause = str(call_args.whereclause)
    assert "token_hash" in where_clause
    assert "expires_at" in where_clause
    assert "used" in where_clause
