"""Test auth registration endpoints."""
from __future__ import annotations

import uuid
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException, Request, status

from app.api.endpoints.auth import Auth
from app.domain.schemas.user import UserCreate
from app.models.user import User
from app.usecase.auth_usecase import DuplicateError


class TestAuthRegistrationEndpoints:
    """Test auth registration endpoints."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_endpoint, mock_auth_usecase):
        """Test successful user registration."""
        # Setup
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "127.0.0.1"

        background_tasks = Mock()

        user_payload = UserCreate(
            username="testuser", email="test@example.com", password="StrongP@ss123"
        )

        created_user = User(
            id=uuid.uuid4(),
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
        )

        mock_auth_usecase.register.return_value = created_user

        with patch("app.api.endpoints.auth.Audit") as mock_audit:
            # Execute
            result = await Auth.register_user(request, user_payload, background_tasks)

            # Assert
            assert result == created_user
            mock_auth_usecase.register.assert_awaited_once_with(
                user_payload, background_tasks=background_tasks
            )
            mock_audit.info.assert_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_register_user_duplicate_error(
        self, auth_endpoint, mock_auth_usecase
    ):
        """Test registration with duplicate error."""
        # Setup
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "127.0.0.1"

        background_tasks = Mock()

        user_payload = UserCreate(
            username="testuser", email="test@example.com", password="StrongP@ss123"
        )

        mock_auth_usecase.register.side_effect = DuplicateError("username")

        with patch("app.api.endpoints.auth.Audit") as mock_audit:
            # Execute and Assert
            with pytest.raises(HTTPException) as excinfo:
                await Auth.register_user(request, user_payload, background_tasks)

            assert excinfo.value.status_code == status.HTTP_409_CONFLICT
            assert excinfo.value.detail == "username already exists"
            mock_auth_usecase.register.assert_awaited_once_with(
                user_payload, background_tasks=background_tasks
            )
            mock_audit.error.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_register_user_weak_password(self, auth_endpoint, mock_auth_usecase):
        """Test registration with weak password - now handled by Pydantic validation."""
        # Setup
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "127.0.0.1"

        Mock()

        # With the updated schema, weak passwords are caught at Pydantic validation level
        # This test now validates that ValidationError is raised during schema creation
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as excinfo:
            UserCreate(username="testuser", email="test@example.com", password="weak")

        # Ensure the error is related to password strength
        assert "strength requirements" in str(excinfo.value)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_register_user_unexpected_error(
        self, auth_endpoint, mock_auth_usecase
    ):
        """Test registration with unexpected error."""
        # Setup
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "127.0.0.1"

        background_tasks = Mock()

        user_payload = UserCreate(
            username="testuser", email="test@example.com", password="StrongP@ss123"
        )

        mock_auth_usecase.register.side_effect = Exception("Unexpected error")

        with patch("app.api.endpoints.auth.Audit") as mock_audit:
            # Execute and Assert
            with pytest.raises(Exception) as excinfo:
                await Auth.register_user(request, user_payload, background_tasks)

            assert str(excinfo.value) == "Unexpected error"
            mock_auth_usecase.register.assert_awaited_once_with(
                user_payload, background_tasks=background_tasks
            )
            mock_audit.error.assert_called_once()
