"""
Usecase fixtures for testing.

This module provides fixtures for testing usecases with dependency injection,
including both mock usecases and real usecases with mocked dependencies.
"""

from unittest.mock import Mock

import pytest

# === USECASE FIXTURES WITH DI ===


@pytest.fixture
def email_verification_usecase_with_di(
    mock_email_verification_repository,
    mock_user_repository,
    mock_refresh_token_repository,
    mock_email_service,
    mock_jwt_utils,
    mock_config,
    mock_audit,
):
    """Create EmailVerificationUsecase with mocked dependencies."""
    from app.usecase.email_verification_usecase import EmailVerificationUsecase

    return EmailVerificationUsecase(
        mock_email_verification_repository,
        mock_user_repository,
        mock_refresh_token_repository,
        mock_email_service,
        mock_jwt_utils,
        mock_config,
        mock_audit,
    )


@pytest.fixture
def mock_email_verification_usecase():
    """Mock EmailVerificationUsecase."""
    from app.usecase.email_verification_usecase import EmailVerificationUsecase

    return Mock(spec=EmailVerificationUsecase)


@pytest.fixture
def wallet_usecase_with_di(
    mock_wallet_repository,
    mock_user_repository,
    mock_portfolio_snapshot_repository,
    mock_config,
    mock_audit,
):
    """Create WalletUsecase with mocked dependencies."""
    from app.usecase.wallet_usecase import WalletUsecase

    return WalletUsecase(
        mock_wallet_repository,
        mock_user_repository,
        mock_portfolio_snapshot_repository,
        mock_config,
        mock_audit,
    )


@pytest.fixture
def oauth_usecase_with_di(
    mock_oauth_account_repository,
    mock_user_repository,
    mock_refresh_token_repository,
    mock_config,
    mock_audit,
):
    """Create OAuthUsecase with mocked dependencies."""
    from app.usecase.oauth_usecase import OAuthUsecase

    return OAuthUsecase(
        mock_oauth_account_repository,
        mock_user_repository,
        mock_refresh_token_repository,
        mock_config,
        mock_audit,
    )


@pytest.fixture
def token_price_usecase_with_di(
    mock_token_price_repository,
    mock_config,
    mock_audit,
):
    """Create TokenPriceUsecase with mocked dependencies."""
    from app.usecase.token_price_usecase import TokenPriceUsecase

    return TokenPriceUsecase(
        mock_token_price_repository,
        mock_config,
        mock_audit,
    )


@pytest.fixture
def token_usecase_with_di(
    mock_token_repository,
    mock_config,
    mock_audit,
):
    """Create TokenUsecase with mocked dependencies."""
    from app.usecase.token_usecase import TokenUsecase

    return TokenUsecase(
        mock_token_repository,
        mock_config,
        mock_audit,
    )


@pytest.fixture
def historical_balance_usecase_with_di(
    mock_historical_balance_repository,
    mock_config,
    mock_audit,
):
    """Create HistoricalBalanceUsecase with mocked dependencies."""
    from app.usecase.historical_balance_usecase import HistoricalBalanceUsecase

    return HistoricalBalanceUsecase(
        mock_historical_balance_repository,
        mock_config,
        mock_audit,
    )


@pytest.fixture
def token_balance_usecase_with_di(
    mock_token_balance_repository,
    mock_config,
    mock_audit,
):
    """Create TokenBalanceUsecase with mocked dependencies."""
    from app.usecase.token_balance_usecase import TokenBalanceUsecase

    return TokenBalanceUsecase(
        mock_token_balance_repository,
        mock_config,
        mock_audit,
    )


@pytest.fixture
def portfolio_snapshot_usecase_with_di(
    mock_portfolio_snapshot_repository,
    mock_wallet_repository,
    mock_audit,
):
    """Create PortfolioSnapshotUsecase with mocked dependencies."""
    from app.usecase.portfolio_snapshot_usecase import PortfolioSnapshotUsecase

    return PortfolioSnapshotUsecase(
        mock_portfolio_snapshot_repository,
        mock_wallet_repository,
        mock_audit,
    )
