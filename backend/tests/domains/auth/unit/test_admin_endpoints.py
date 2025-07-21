from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.api.endpoints import admin
from app.api.endpoints.admin import Admin
from app.models.user import User


@pytest.fixture
def mock_user_repository():
    """Mock UserRepository for testing."""
    mock_repo = Mock()
    mock_repo.get_all = AsyncMock()
    mock_repo.get_by_id = AsyncMock()
    mock_repo.save = AsyncMock()
    return mock_repo


@pytest.fixture
def admin_endpoint(mock_user_repository):
    """Create Admin endpoint instance with mocked dependencies."""
    return Admin(mock_user_repository)


@pytest.mark.asyncio
async def test_list_users_success(admin_endpoint, mock_user_repository):
    # Setup
    # Mock users data
    mock_users = [
        User(id=uuid.uuid4(), username="user1", email="user1@example.com"),
        User(id=uuid.uuid4(), username="user2", email="user2@example.com"),
    ]
    mock_user_repository.get_all.return_value = mock_users

    # Mock current user with admin role
    User(id=uuid.uuid4(), username="admin", email="admin@example.com", roles=["admin"])

    # Execute - call the static method directly
    result = await Admin.list_users()

    # Assert
    assert "users" in result
    assert len(result["users"]) == 2
    assert result["users"][0]["username"] == "user1"
    assert result["users"][1]["username"] == "user2"
    mock_user_repository.get_all.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_analytics_admin_role():
    # Setup
    # Mock current user with admin role
    current_user = User(
        id=uuid.uuid4(), username="admin", email="admin@example.com", roles=["admin"]
    )
    # Set roles for testing
    current_user._current_roles = ["admin"]

    # Execute
    result = await Admin.get_analytics(current_user)

    # Assert
    assert "user_roles" in result
    assert "analytics" in result
    assert "admin" in result["user_roles"]
    assert "total_portfolios" in result["analytics"]
    assert "total_volume" in result["analytics"]
    assert "active_traders" in result["analytics"]


@pytest.mark.asyncio
async def test_get_analytics_fund_manager_role():
    # Setup
    # Mock current user with fund_manager role
    current_user = User(
        id=uuid.uuid4(),
        username="manager",
        email="manager@example.com",
        roles=["fund_manager"],
    )
    # Set roles for testing
    current_user._current_roles = ["fund_manager"]

    # Execute
    result = await Admin.get_analytics(current_user)

    # Assert
    assert "user_roles" in result
    assert "analytics" in result
    assert "fund_manager" in result["user_roles"]
    assert "total_portfolios" in result["analytics"]
    assert "total_volume" in result["analytics"]
    assert "active_traders" in result["analytics"]


@pytest.mark.asyncio
async def test_high_value_operations_success():
    # Setup
    # Mock current user with required attributes
    current_user = User(
        id=uuid.uuid4(), username="wealthy", email="wealthy@example.com"
    )
    # Set attributes for testing
    current_user._current_attributes = {
        "portfolio_value": 2000000,
        "kyc_level": "verified",
    }

    # Execute
    result = await Admin.high_value_operations(current_user)

    # Assert
    assert "user_attributes" in result
    assert "operations" in result
    assert result["user_attributes"]["portfolio_value"] == 2000000
    assert result["user_attributes"]["kyc_level"] == "verified"
    assert len(result["operations"]) == 3
    assert any(op["type"] == "institutional_trading" for op in result["operations"])
    assert any(op["type"] == "large_block_trading" for op in result["operations"])
    assert any(op["type"] == "otc_trading" for op in result["operations"])


@pytest.mark.asyncio
async def test_regional_features_us():
    # Setup
    # Mock current user with US geography
    current_user = User(id=uuid.uuid4(), username="us_user", email="us@example.com")
    # Set attributes for testing
    current_user._current_attributes = {"geography": "US"}

    # Execute
    result = await Admin.regional_features(current_user)

    # Assert
    assert "geography" in result
    assert "available_features" in result
    assert result["geography"] == "US"
    assert "advanced_options" in result["available_features"]
    assert "crypto_futures" in result["available_features"]
    assert "margin_trading" in result["available_features"]


@pytest.mark.asyncio
async def test_regional_features_ca():
    # Setup
    # Mock current user with CA geography
    current_user = User(id=uuid.uuid4(), username="ca_user", email="ca@example.com")
    # Set attributes for testing
    current_user._current_attributes = {"geography": "CA"}

    # Execute
    result = await Admin.regional_features(current_user)

    # Assert
    assert "geography" in result
    assert "available_features" in result
    assert result["geography"] == "CA"
    assert "basic_options" in result["available_features"]
    assert "crypto_trading" in result["available_features"]
    assert "tfsa_accounts" in result["available_features"]


@pytest.mark.asyncio
async def test_regional_features_eu():
    # Setup
    # Mock current user with EU geography
    current_user = User(id=uuid.uuid4(), username="eu_user", email="eu@example.com")
    # Set attributes for testing
    current_user._current_attributes = {"geography": "EU"}

    # Execute
    result = await Admin.regional_features(current_user)

    # Assert
    assert "geography" in result
    assert "available_features" in result
    assert result["geography"] == "EU"
    assert "mifid_products" in result["available_features"]
    assert "crypto_trading" in result["available_features"]
    assert "regulated_investing" in result["available_features"]


@pytest.mark.asyncio
async def test_regional_features_unknown():
    # Setup
    # Mock current user with unknown geography
    current_user = User(
        id=uuid.uuid4(), username="unknown_user", email="unknown@example.com"
    )
    # Set attributes for testing
    current_user._current_attributes = {"geography": "unknown"}

    # Execute
    result = await Admin.regional_features(current_user)

    # Assert
    assert "geography" in result
    assert "available_features" in result
    assert result["geography"] == "unknown"
    assert result["available_features"] == ["basic_trading"]


@pytest.mark.asyncio
async def test_get_system_health():
    # Setup
    # Mock current user with admin role
    current_user = User(
        id=uuid.uuid4(), username="admin", email="admin@example.com", roles=["admin"]
    )
    # Set roles for testing
    current_user._current_roles = ["admin"]

    # Execute
    result = await Admin.get_system_health(current_user)

    # Assert
    assert "status" in result
    assert "uptime" in result
    assert "services" in result
    assert "accessed_by" in result
    assert result["status"] == "healthy"
    assert result["services"]["database"] == "up"
    assert result["services"]["redis"] == "up"
    assert result["services"]["blockchain"] == "up"
    assert result["accessed_by"]["user_id"] == str(current_user.id)
    assert "admin" in result["accessed_by"]["roles"]


@pytest.mark.asyncio
async def test_assign_user_role_success(admin_endpoint, mock_user_repository):
    # Setup
    user_id = str(uuid.uuid4())
    role = "admin"

    # Mock user data
    mock_user = User(
        id=uuid.UUID(user_id),
        username="testuser",
        email="test@example.com",
        roles=["individual_investor"],
    )
    mock_user_repository.get_by_id.return_value = mock_user
    mock_user_repository.save.return_value = None

    # Mock current user with admin role
    current_user = User(
        id=uuid.uuid4(), username="admin", email="admin@example.com", roles=["admin"]
    )

    # Execute
    result = await Admin.assign_user_role(user_id, role, current_user)

    # Assert
    assert "message" in result
    assert "user_roles" in result
    assert "assigned_by" in result
    assert role in result["user_roles"]
    assert result["assigned_by"] == str(current_user.id)
    mock_user_repository.get_by_id.assert_awaited_once_with(user_id)
    mock_user_repository.save.assert_awaited_once_with(mock_user)


@pytest.mark.asyncio
async def test_assign_user_role_invalid_role(admin_endpoint, mock_user_repository):
    # Setup
    user_id = str(uuid.uuid4())
    invalid_role = "invalid_role"

    # Mock current user with admin role
    current_user = User(
        id=uuid.uuid4(), username="admin", email="admin@example.com", roles=["admin"]
    )

    # Execute & Assert
    with pytest.raises(Exception):  # HTTPException
        await Admin.assign_user_role(user_id, invalid_role, current_user)


@pytest.mark.asyncio
async def test_assign_user_role_user_not_found(admin_endpoint, mock_user_repository):
    # Setup
    user_id = str(uuid.uuid4())
    role = "admin"

    # Mock user not found
    mock_user_repository.get_by_id.return_value = None

    # Mock current user with admin role
    current_user = User(
        id=uuid.uuid4(), username="admin", email="admin@example.com", roles=["admin"]
    )

    # Execute & Assert
    with pytest.raises(Exception):  # HTTPException
        await Admin.assign_user_role(user_id, role, current_user)


@pytest.mark.asyncio
async def test_assign_user_role_database_error(admin_endpoint, mock_user_repository):
    # Setup
    user_id = str(uuid.uuid4())
    role = "admin"

    # Mock user data
    mock_user = User(
        id=uuid.UUID(user_id),
        username="testuser",
        email="test@example.com",
        roles=["individual_investor"],
    )
    mock_user_repository.get_by_id.return_value = mock_user
    mock_user_repository.save.side_effect = Exception("Database error")

    # Mock current user with admin role
    current_user = User(
        id=uuid.uuid4(), username="admin", email="admin@example.com", roles=["admin"]
    )

    # Execute & Assert
    with pytest.raises(Exception):  # HTTPException
        await Admin.assign_user_role(user_id, role, current_user)


@pytest.mark.asyncio
async def test_get_user_profile():
    # Setup
    user_id = uuid.uuid4()
    current_user = User(
        id=user_id,
        username="testuser",
        email="test@example.com",
        roles=["individual_investor"],
    )

    # Mock request with user_id and token payload
    payload = {
        "sub": str(user_id),
        "roles": ["individual_investor"],
        "attributes": {"portfolio_value": 50000, "kyc_level": "basic"},
    }
    request = Mock(state=Mock(user_id=user_id, token_payload=payload))

    # Mock the DIContainer and database service
    mock_session_context = AsyncMock()
    mock_session_context.__aenter__.return_value = Mock(
        get=AsyncMock(return_value=current_user)
    )

    mock_database = Mock()
    mock_database.get_session.return_value = mock_session_context

    mock_di_container = Mock()
    mock_di_container.get_core.return_value = mock_database

    with patch("app.main.di_container", mock_di_container):
        # Execute
        result = await Admin.get_user_profile(request)

        # Assert
        assert "user_id" in result
        assert "username" in result
        assert "email" in result
        assert "roles" in result
        assert "attributes" in result
        assert "permissions" in result
        assert result["user_id"] == str(current_user.id)
        assert result["username"] == "testuser"
        assert result["email"] == "test@example.com"
        assert "individual_investor" in result["roles"]
        assert result["attributes"]["portfolio_value"] == 50000
        assert result["attributes"]["kyc_level"] == "basic"
