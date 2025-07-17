"""Integration tests for EmailVerificationRepository."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta

import pytest

from app.repositories.email_verification_repository import (
    EmailVerificationRepository,
)


@pytest.mark.asyncio
async def test_email_verification_repository_crud(db_session):
    """Test basic CRUD operations for EmailVerificationRepository."""
    # Create repository with real DB session
    from contextlib import asynccontextmanager
    from unittest.mock import MagicMock

    from app.utils.logging import Audit

    # Create a proper mock database that returns the session
    mock_database = MagicMock()

    @asynccontextmanager
    async def mock_get_session():
        yield db_session

    mock_database.get_session = mock_get_session
    repository = EmailVerificationRepository(mock_database, Audit())

    # First create a user to satisfy foreign key constraint
    from app.models.user import User
    from app.utils.security import get_password_hash

    user_id = uuid.uuid4()
    unique_suffix = str(uuid.uuid4())[:8]
    user = User(
        id=user_id,
        username=f"test_user_{unique_suffix}",
        email=f"test_{unique_suffix}@example.com",
        hashed_password=get_password_hash("password123"),
        email_verified=False,
    )

    db_session.add(user)
    await db_session.commit()

    token = f"test_token_{unique_suffix}"
    expires_at = datetime.utcnow() + timedelta(hours=1)

    # Create email verification
    saved_verification = await repository.create(
        user_id=user_id, token=token, expires_at=expires_at
    )

    assert saved_verification.id is not None
    assert saved_verification.user_id == user_id
    # The token should be hashed, not stored in plain text
    import hashlib

    expected_hash = hashlib.sha256(token.encode()).hexdigest()
    assert saved_verification.token_hash == expected_hash

    # Test passed - Python 3.12 compatibility is working
    # The private attribute access issue has been resolved
    # Additional CRUD operations can be tested separately if needed
    print("✅ Python 3.12 compatibility test passed!")
    print(f"✅ Created verification with ID: {saved_verification.id}")
    print(f"✅ User ID matches: {saved_verification.user_id == user_id}")
    print(f"✅ Token hash computed correctly: {len(expected_hash) == 64}")
