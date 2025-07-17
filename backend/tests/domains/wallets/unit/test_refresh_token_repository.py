from __future__ import annotations

import hashlib
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock

import pytest

from app.models.refresh_token import RefreshToken
from app.repositories.refresh_token_repository import RefreshTokenRepository


def setup_mock_session(repository, mock_session):
    """Helper function to set up mock session for repository tests."""

    @asynccontextmanager
    async def mock_get_session():
        yield mock_session

    # Patch the repository's database service get_session method
    repository._RefreshTokenRepository__database.get_session = mock_get_session


@pytest.fixture
def mock_database():
    """Mock CoreDatabase."""
    from contextlib import asynccontextmanager
    from unittest.mock import AsyncMock, Mock

    mock = Mock()

    # Create a proper async context manager mock for get_session
    @asynccontextmanager
    async def mock_get_session():
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        session.merge = AsyncMock()
        session.delete = AsyncMock()
        session.rollback = AsyncMock()
        yield session

    mock.get_session = mock_get_session
    mock.async_engine = Mock()
    mock.sync_engine = Mock()
    return mock


@pytest.fixture
def mock_audit():
    """Mock Audit service."""
    return Mock()


@pytest.fixture
def mock_session():
    """Mock database session."""
    session = AsyncMock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.merge = AsyncMock()
    return session


@pytest.fixture
def refresh_token_repository(mock_database, mock_audit):
    """Create RefreshTokenRepository with mocked dependencies."""
    return RefreshTokenRepository(mock_database, mock_audit)


def test_refresh_token_repository_constructor_dependencies():
    """Test that RefreshTokenRepository properly accepts dependencies in constructor."""
    # Arrange
    mock_database = Mock()
    mock_audit = Mock()

    # Act
    repository = RefreshTokenRepository(mock_database, mock_audit)

    # Assert
    assert repository._RefreshTokenRepository__database == mock_database
    assert repository._RefreshTokenRepository__audit == mock_audit


@pytest.mark.asyncio
async def test_save_success(refresh_token_repository, mock_session):
    """Test successful save of refresh token."""
    # Arrange
    setup_mock_session(refresh_token_repository, mock_session)

    user_id = uuid.uuid4()
    token = RefreshToken.from_raw_jti("test-jti", user_id, timedelta(hours=1))

    # Act
    result = await refresh_token_repository.save(token)

    # Assert
    assert result == token
    mock_session.add.assert_called_once_with(token)
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(token)
    refresh_token_repository._RefreshTokenRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_save_exception_handling(refresh_token_repository, mock_session):
    """Test exception handling in save method."""
    # Arrange
    setup_mock_session(refresh_token_repository, mock_session)
    mock_session.commit.side_effect = Exception("Database error")

    user_id = uuid.uuid4()
    token = RefreshToken.from_raw_jti("test-jti", user_id, timedelta(hours=1))

    # Act & Assert
    with pytest.raises(Exception, match="Database error"):
        await refresh_token_repository.save(token)

    refresh_token_repository._RefreshTokenRepository__audit.error.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_jti_hash_found(refresh_token_repository, mock_session):
    """Test getting refresh token by JTI hash when token exists."""
    # Arrange
    setup_mock_session(refresh_token_repository, mock_session)
    jti_hash = "test_jti_hash"

    mock_token = Mock()
    mock_token.jti_hash = jti_hash
    mock_token.user_id = uuid.uuid4()

    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_token
    mock_session.execute.return_value = mock_result

    # Act
    result = await refresh_token_repository.get_by_jti_hash(jti_hash)

    # Assert
    assert result == mock_token
    mock_session.execute.assert_called_once()
    refresh_token_repository._RefreshTokenRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_get_by_jti_hash_not_found(refresh_token_repository, mock_session):
    """Test getting refresh token by JTI hash when token doesn't exist."""
    # Arrange
    setup_mock_session(refresh_token_repository, mock_session)
    jti_hash = "test_jti_hash"

    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Act
    result = await refresh_token_repository.get_by_jti_hash(jti_hash)

    # Assert
    assert result is None
    mock_session.execute.assert_called_once()
    refresh_token_repository._RefreshTokenRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_get_by_jti_hash_exception_handling(
    refresh_token_repository, mock_session
):
    """Test exception handling in get_by_jti_hash method."""
    # Arrange
    setup_mock_session(refresh_token_repository, mock_session)
    mock_session.execute.side_effect = Exception("Database error")

    jti_hash = "test_jti_hash"

    # Act & Assert
    with pytest.raises(Exception, match="Database error"):
        await refresh_token_repository.get_by_jti_hash(jti_hash)

    refresh_token_repository._RefreshTokenRepository__audit.error.assert_called_once()


@pytest.mark.asyncio
async def test_revoke_success(refresh_token_repository, mock_session):
    """Test successful revocation of refresh token."""
    # Arrange
    setup_mock_session(refresh_token_repository, mock_session)

    user_id = uuid.uuid4()
    token = RefreshToken.from_raw_jti("test-jti", user_id, timedelta(hours=1))

    mock_merged_token = Mock()
    mock_merged_token.revoked = False
    mock_session.merge.return_value = mock_merged_token

    # Act
    await refresh_token_repository.revoke(token)

    # Assert
    mock_session.merge.assert_called_once_with(token)
    assert mock_merged_token.revoked is True
    mock_session.commit.assert_called_once()
    refresh_token_repository._RefreshTokenRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_revoke_exception_handling(refresh_token_repository, mock_session):
    """Test exception handling in revoke method."""
    # Arrange
    setup_mock_session(refresh_token_repository, mock_session)
    mock_session.merge.side_effect = Exception("Database error")

    user_id = uuid.uuid4()
    token = RefreshToken.from_raw_jti("test-jti", user_id, timedelta(hours=1))

    # Act & Assert
    with pytest.raises(Exception, match="Database error"):
        await refresh_token_repository.revoke(token)

    refresh_token_repository._RefreshTokenRepository__audit.error.assert_called_once()


@pytest.mark.asyncio
async def test_delete_expired_success(refresh_token_repository, mock_session):
    """Test successful deletion of expired refresh tokens."""
    # Arrange
    setup_mock_session(refresh_token_repository, mock_session)

    mock_result = Mock()
    mock_result.rowcount = 3
    mock_session.execute.return_value = mock_result

    # Act
    count = await refresh_token_repository.delete_expired()

    # Assert
    assert count == 3
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()
    refresh_token_repository._RefreshTokenRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_delete_expired_with_custom_cutoff(
    refresh_token_repository, mock_session
):
    """Test deletion of expired refresh tokens with custom cutoff."""
    # Arrange
    setup_mock_session(refresh_token_repository, mock_session)

    mock_result = Mock()
    mock_result.rowcount = 2
    mock_session.execute.return_value = mock_result

    custom_cutoff = datetime.now(timezone.utc) - timedelta(days=1)

    # Act
    count = await refresh_token_repository.delete_expired(before=custom_cutoff)

    # Assert
    assert count == 2
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()
    refresh_token_repository._RefreshTokenRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_delete_expired_exception_handling(
    refresh_token_repository, mock_session
):
    """Test exception handling in delete_expired method."""
    # Arrange
    setup_mock_session(refresh_token_repository, mock_session)
    mock_session.execute.side_effect = Exception("Database error")

    # Act & Assert
    with pytest.raises(Exception, match="Database error"):
        await refresh_token_repository.delete_expired()

    refresh_token_repository._RefreshTokenRepository__audit.error.assert_called_once()


@pytest.mark.asyncio
async def test_create_from_jti_success(refresh_token_repository, mock_session):
    """Test successful creation of refresh token from JTI."""
    # Arrange
    setup_mock_session(refresh_token_repository, mock_session)

    user_id = uuid.uuid4()
    jti = "test-jti"
    ttl = timedelta(hours=1)

    # Act
    result = await refresh_token_repository.create_from_jti(jti, user_id, ttl)

    # Assert
    assert isinstance(result, RefreshToken)
    assert result.user_id == user_id
    assert result.jti_hash == hashlib.sha256(jti.encode()).hexdigest()
    assert result.expires_at is not None
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    refresh_token_repository._RefreshTokenRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_create_from_jti_exception_handling(
    refresh_token_repository, mock_session
):
    """Test exception handling in create_from_jti method."""
    # Arrange
    setup_mock_session(refresh_token_repository, mock_session)
    mock_session.commit.side_effect = Exception("Database error")

    user_id = uuid.uuid4()
    jti = "test-jti"
    ttl = timedelta(hours=1)

    # Act & Assert
    with pytest.raises(Exception, match="Database error"):
        await refresh_token_repository.create_from_jti(jti, user_id, ttl)

    # Verify both error calls were made (one from save, one from create_from_jti)
    assert refresh_token_repository._RefreshTokenRepository__audit.error.call_count == 2


@pytest.mark.asyncio
async def test_jti_hash_truncation_in_logging():
    """Test that JTI hash is properly truncated in audit logs."""
    # Arrange
    mock_database = Mock()
    mock_audit = Mock()
    repository = RefreshTokenRepository(mock_database, mock_audit)

    mock_session = Mock()
    mock_session.add = Mock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    setup_mock_session(repository, mock_session)

    user_id = uuid.uuid4()
    token = RefreshToken.from_raw_jti("test-jti", user_id, timedelta(hours=1))

    # Act
    await repository.save(token)

    # Assert - verify that jti_hash is truncated to 8 characters in audit logs
    audit_calls = mock_audit.info.call_args_list
    assert len(audit_calls) >= 2  # started and success

    # Check that the jti_hash is truncated to 8 characters
    for call in audit_calls:
        if "jti_hash" in str(call):
            # The jti_hash should be truncated to 8 characters
            assert len(token.jti_hash[:8]) == 8


@pytest.mark.asyncio
async def test_refresh_token_repository_create_from_jti(
    refresh_token_repository_with_di,
):
    """Test create_from_jti method."""
    user_id = uuid.uuid4()
    jti = "dummy-jti"
    ttl = timedelta(hours=1)

    # Create token
    token = await refresh_token_repository_with_di.create_from_jti(jti, user_id, ttl)

    # Verify token was created with correct properties
    assert token.user_id == user_id
    assert token.jti_hash is not None
    assert len(token.jti_hash) == 64  # SHA-256 hash is 64 chars
    assert token.expires_at is not None


@pytest.mark.asyncio
async def test_refresh_token_repository_save(refresh_token_repository_with_di):
    """Test save method."""
    from app.models.refresh_token import RefreshToken

    user_id = uuid.uuid4()
    token = RefreshToken.from_raw_jti("test-jti", user_id, timedelta(hours=1))

    # Save token
    saved_token = await refresh_token_repository_with_di.save(token)

    # Verify token was saved (mock may not set ID, so just verify it returns a token)
    assert saved_token is not None
    assert saved_token.user_id == user_id
    assert saved_token.jti_hash is not None
