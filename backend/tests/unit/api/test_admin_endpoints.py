from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.endpoints import admin
from app.core.security.roles import Permission, UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository


@pytest.mark.asyncio
async def test_list_users_success():
    # Setup
    db = AsyncMock(spec=AsyncSession)

    # Create mock users
    user1 = User(id=uuid.uuid4(), username="user1", email="user1@example.com")
    user2 = User(id=uuid.uuid4(), username="user2", email="user2@example.com")
    users = [user1, user2]

    # Create mock repository
    mock_repo = AsyncMock(spec=UserRepository)
    mock_repo.get_all.return_value = users

    # Mock current user with admin role
    current_user = User(
        id=uuid.uuid4(), username="admin", email="admin@example.com", roles=["admin"]
    )

    # Mock UserRepository constructor
    with patch("app.api.endpoints.admin.UserRepository", return_value=mock_repo):
        # Execute
        result = await admin.list_users(db, current_user)

        # Assert
        assert "users" in result
        assert len(result["users"]) == 2
        assert result["users"][0]["username"] == "user1"
        assert result["users"][1]["username"] == "user2"
        mock_repo.get_all.assert_awaited_once()


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
    result = await admin.get_analytics(current_user)

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
    result = await admin.get_analytics(current_user)

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
    result = await admin.high_value_operations(current_user)

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
    result = await admin.regional_features(current_user)

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
    result = await admin.regional_features(current_user)

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
    result = await admin.regional_features(current_user)

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
    result = await admin.regional_features(current_user)

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
    result = await admin.get_system_health(current_user)

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
async def test_assign_user_role_success():
    # Setup
    db = AsyncMock(spec=AsyncSession)

    # Create target user
    user_id = str(uuid.uuid4())
    target_user = User(
        id=uuid.UUID(user_id), username="target", email="target@example.com", roles=[]
    )

    # Create admin user
    admin_user = User(
        id=uuid.uuid4(), username="admin", email="admin@example.com", roles=["admin"]
    )

    # Create mock repository
    mock_repo = AsyncMock(spec=UserRepository)
    mock_repo.get_by_id.return_value = target_user
    mock_repo.save.return_value = None

    # Mock UserRepository constructor
    with patch("app.api.endpoints.admin.UserRepository", return_value=mock_repo):
        # Execute
        result = await admin.assign_user_role(user_id, "trader", db, admin_user)

        # Assert
        assert "message" in result
        assert "user_roles" in result
        assert "assigned_by" in result
        assert "trader" in result["user_roles"]
        assert result["assigned_by"] == str(admin_user.id)
        mock_repo.get_by_id.assert_awaited_once_with(user_id)
        mock_repo.save.assert_awaited_once_with(target_user)


@pytest.mark.asyncio
async def test_assign_user_role_invalid_role():
    # Setup
    db = AsyncMock(spec=AsyncSession)

    # Create admin user
    admin_user = User(
        id=uuid.uuid4(), username="admin", email="admin@example.com", roles=["admin"]
    )

    # Execute and Assert
    with pytest.raises(HTTPException) as excinfo:
        await admin.assign_user_role("some-id", "invalid_role", db, admin_user)

    assert excinfo.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid role" in excinfo.value.detail


@pytest.mark.asyncio
async def test_assign_user_role_user_not_found():
    # Setup
    db = AsyncMock(spec=AsyncSession)

    # Create admin user
    admin_user = User(
        id=uuid.uuid4(), username="admin", email="admin@example.com", roles=["admin"]
    )

    # Create mock repository
    mock_repo = AsyncMock(spec=UserRepository)
    mock_repo.get_by_id.return_value = None

    # Mock UserRepository constructor
    with patch("app.api.endpoints.admin.UserRepository", return_value=mock_repo):
        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await admin.assign_user_role(str(uuid.uuid4()), "trader", db, admin_user)

        assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND
        assert excinfo.value.detail == "User not found"


@pytest.mark.asyncio
async def test_assign_user_role_database_error():
    # Setup
    db = AsyncMock(spec=AsyncSession)

    # Create target user
    user_id = str(uuid.uuid4())
    target_user = User(
        id=uuid.UUID(user_id), username="target", email="target@example.com", roles=[]
    )

    # Create admin user
    admin_user = User(
        id=uuid.uuid4(), username="admin", email="admin@example.com", roles=["admin"]
    )

    # Create mock repository
    mock_repo = AsyncMock(spec=UserRepository)
    mock_repo.get_by_id.return_value = target_user
    mock_repo.save.side_effect = Exception("Database error")

    # Mock UserRepository constructor
    with patch("app.api.endpoints.admin.UserRepository", return_value=mock_repo):
        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await admin.assign_user_role(user_id, "trader", db, admin_user)

        assert excinfo.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to assign role" in excinfo.value.detail


@pytest.mark.asyncio
async def test_get_user_profile():
    # Setup
    # Mock current user with roles and attributes
    current_user = User(
        id=uuid.uuid4(), username="testuser", email="test@example.com", roles=["trader"]
    )
    # Set roles and attributes for testing
    current_user._current_roles = ["trader"]
    current_user._current_attributes = {"portfolio_value": 500000, "kyc_level": "basic"}

    # Execute
    result = await admin.get_user_profile(current_user)

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
    assert "trader" in result["roles"]
    assert result["attributes"]["portfolio_value"] == 500000
    assert result["attributes"]["kyc_level"] == "basic"
    assert "wallet" in result["permissions"]
