"""
Service-specific test fixtures.

This module provides fixtures for testing service classes and their dependencies.
"""

from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_contract():
    """Create mock contract instance."""
    contract = Mock()
    contract.functions = Mock()
    return contract


@pytest.fixture
def oauth_service_with_di(
    mock_user_repository,
    mock_oauth_account_repository,
    mock_refresh_token_repository,
    mock_jwt_utils,
    mock_config,
    mock_audit,
):
    """Create OAuthService with mocked dependencies."""
    from app.services.oauth_service import OAuthService

    return OAuthService(
        user_repo=mock_user_repository,
        oauth_account_repo=mock_oauth_account_repository,
        refresh_token_repo=mock_refresh_token_repository,
        jwt_utils=mock_jwt_utils,
        config=mock_config,
        audit=mock_audit,
    )


@pytest.fixture
def email_service_with_di(mock_config, mock_audit):
    """Create EmailService with mocked dependencies."""
    from app.services.email_service import EmailService

    return EmailService(config=mock_config, audit=mock_audit)
