from __future__ import annotations

import hashlib
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy import select

from app.models.password_reset import PasswordReset
from app.repositories.password_reset_repository import PasswordResetRepository


def setup_mock_session(repository, mock_session):
    """Helper function to set up mock session for repository tests."""

    @asynccontextmanager
    async def mock_get_session():
        yield mock_session

    # Patch the repository's database service get_session method
    repository._PasswordResetRepository__database.get_session = mock_get_session


@pytest.fixture
def mock_database():
    """Mock CoreDatabase."""
    return Mock()


@pytest.fixture
def mock_audit():
    """Mock Audit service."""
    return Mock()


@pytest.fixture
def mock_session():
    """Mock database session."""
    session = Mock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.merge = AsyncMock()
    return session


@pytest.fixture
def password_reset_repository(mock_database, mock_audit):
    """Create PasswordResetRepository with mocked dependencies."""
    return PasswordResetRepository(mock_database, mock_audit)


def test_password_reset_repository_constructor_dependencies():
    """Test that PasswordResetRepository properly accepts dependencies in constructor."""
    # Arrange
    mock_database = Mock()
    mock_audit = Mock()

    # Act
    repository = PasswordResetRepository(mock_database, mock_audit)

    # Assert
    assert repository._PasswordResetRepository__database == mock_database
    assert repository._PasswordResetRepository__audit == mock_audit


@pytest.mark.asyncio
async def test_create_success(password_reset_repository, mock_session):
    """Test successful creation of password reset token."""
    # Arrange
    setup_mock_session(password_reset_repository, mock_session)
    token = "test_token"
    user_id = uuid.uuid4()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Act
    result = await password_reset_repository.create(token, user_id, expires_at)
    
    # Assert
    assert isinstance(result, PasswordReset)
    assert result.token_hash == hashlib.sha256(token.encode()).hexdigest()
    assert result.user_id == user_id
    assert result.expires_at == expires_at
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()
    password_reset_repository._PasswordResetRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_create_exception_handling(password_reset_repository, mock_session):
    """Test exception handling in create method."""
    # Arrange
    setup_mock_session(password_reset_repository, mock_session)
    mock_session.commit.side_effect = Exception("Database error")
    
    token = "test_token"
    user_id = uuid.uuid4()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Act & Assert
    with pytest.raises(Exception, match="Database error"):
        await password_reset_repository.create(token, user_id, expires_at)
    
    password_reset_repository._PasswordResetRepository__audit.error.assert_called_once()


@pytest.mark.asyncio
async def test_get_valid_found(password_reset_repository, mock_session):
    """Test getting a valid password reset token that exists."""
    # Arrange
    setup_mock_session(password_reset_repository, mock_session)
    token = "test_token"
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    mock_pr = Mock()
    mock_pr.token_hash = token_hash
    mock_pr.user_id = uuid.uuid4()
    mock_pr.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    mock_pr.used = False
    
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_pr
    mock_session.execute.return_value = mock_result
    
    # Act
    result = await password_reset_repository.get_valid(token)
    
    # Assert
    assert result == mock_pr
    mock_session.execute.assert_called_once()
    password_reset_repository._PasswordResetRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_get_valid_not_found(password_reset_repository, mock_session):
    """Test getting a valid password reset token that doesn't exist."""
    # Arrange
    setup_mock_session(password_reset_repository, mock_session)
    token = "test_token"
    
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    # Act
    result = await password_reset_repository.get_valid(token)
    
    # Assert
    assert result is None
    mock_session.execute.assert_called_once()
    password_reset_repository._PasswordResetRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_get_valid_exception_handling(password_reset_repository, mock_session):
    """Test exception handling in get_valid method."""
    # Arrange
    setup_mock_session(password_reset_repository, mock_session)
    mock_session.execute.side_effect = Exception("Database error")
    
    token = "test_token"
    
    # Act & Assert
    with pytest.raises(Exception, match="Database error"):
        await password_reset_repository.get_valid(token)
    
    password_reset_repository._PasswordResetRepository__audit.error.assert_called_once()


@pytest.mark.asyncio
async def test_mark_used_success(password_reset_repository, mock_session):
    """Test successful marking of password reset token as used."""
    # Arrange
    setup_mock_session(password_reset_repository, mock_session)
    
    mock_pr = Mock()
    mock_pr.token_hash = "test_hash"
    mock_pr.used = False
    
    mock_merged_pr = Mock()
    mock_merged_pr.used = False
    mock_session.merge.return_value = mock_merged_pr
    
    # Act
    await password_reset_repository.mark_used(mock_pr)
    
    # Assert
    mock_session.merge.assert_called_once_with(mock_pr)
    assert mock_merged_pr.used is True
    mock_session.commit.assert_called_once()
    password_reset_repository._PasswordResetRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_mark_used_exception_handling(password_reset_repository, mock_session):
    """Test exception handling in mark_used method."""
    # Arrange
    setup_mock_session(password_reset_repository, mock_session)
    mock_session.merge.side_effect = Exception("Database error")
    
    mock_pr = Mock()
    mock_pr.token_hash = "test_hash"
    
    # Act & Assert
    with pytest.raises(Exception, match="Database error"):
        await password_reset_repository.mark_used(mock_pr)
    
    password_reset_repository._PasswordResetRepository__audit.error.assert_called_once()


@pytest.mark.asyncio
async def test_delete_expired_success(password_reset_repository, mock_session):
    """Test successful deletion of expired password reset tokens."""
    # Arrange
    setup_mock_session(password_reset_repository, mock_session)
    
    mock_result = Mock()
    mock_result.rowcount = 3
    mock_session.execute.return_value = mock_result
    
    # Act
    count = await password_reset_repository.delete_expired()
    
    # Assert
    assert count == 3
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()
    password_reset_repository._PasswordResetRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_delete_expired_exception_handling(password_reset_repository, mock_session):
    """Test exception handling in delete_expired method."""
    # Arrange
    setup_mock_session(password_reset_repository, mock_session)
    mock_session.execute.side_effect = Exception("Database error")
    
    # Act & Assert
    with pytest.raises(Exception, match="Database error"):
        await password_reset_repository.delete_expired()
    
    password_reset_repository._PasswordResetRepository__audit.error.assert_called_once()


@pytest.mark.asyncio
async def test_token_hashing_consistency():
    """Test that token hashing is consistent across methods."""
    # Arrange
    token = "test_token"
    expected_hash = hashlib.sha256(token.encode()).hexdigest()
    
    mock_database = Mock()
    mock_audit = Mock()
    repository = PasswordResetRepository(mock_database, mock_audit)
    
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
    
    # Assert - check that the PasswordReset object was created with correct hash
    call_args = mock_session.add.call_args[0][0]
    assert call_args.token_hash == expected_hash


@pytest.mark.asyncio
async def test_audit_logging_patterns(password_reset_repository, mock_session):
    """Test that audit logging follows consistent patterns."""
    # Arrange
    setup_mock_session(password_reset_repository, mock_session)
    audit_mock = password_reset_repository._PasswordResetRepository__audit
    
    # Test create audit logging
    token = "test_token"
    user_id = uuid.uuid4()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Act
    await password_reset_repository.create(token, user_id, expires_at)
    
    # Assert
    audit_calls = audit_mock.info.call_args_list
    assert len(audit_calls) == 2  # started and success
    assert "password_reset_repository_create_started" in str(audit_calls[0])
    assert "password_reset_repository_create_success" in str(audit_calls[1])


@pytest.mark.asyncio
async def test_get_valid_query_structure(password_reset_repository, mock_session):
    """Test that get_valid builds the correct SQL query structure."""
    # Arrange
    setup_mock_session(password_reset_repository, mock_session)
    token = "test_token"
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    # Act
    await password_reset_repository.get_valid(token)
    
    # Assert
    mock_session.execute.assert_called_once()
    call_args = mock_session.execute.call_args[0][0]
    # The query should be a select statement
    assert hasattr(call_args, 'whereclause')
    # Should have proper where conditions for token_hash, expires_at, and used
    where_clause = str(call_args.whereclause)
    assert "token_hash" in where_clause
    assert "expires_at" in where_clause
    assert "used" in where_clause


@pytest.mark.asyncio
async def test_delete_expired_query_structure(password_reset_repository, mock_session):
    """Test that delete_expired builds the correct SQL query structure."""
    # Arrange
    setup_mock_session(password_reset_repository, mock_session)
    
    mock_result = Mock()
    mock_result.rowcount = 0
    mock_session.execute.return_value = mock_result
    
    # Act
    await password_reset_repository.delete_expired()
    
    # Assert
    mock_session.execute.assert_called_once()
    call_args = mock_session.execute.call_args[0][0]
    # The query should be a delete statement
    assert hasattr(call_args, 'whereclause')
    # Should have proper where condition for expires_at
    where_clause = str(call_args.whereclause)
    assert "expires_at" in where_clause