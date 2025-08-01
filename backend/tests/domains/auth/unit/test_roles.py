"""
Unit tests for RBAC/ABAC role-based and attribute-based access control.

These tests follow TDD approach - they will fail initially and guide the implementation.
"""

from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from app.api.dependencies import (
    require_attributes,
    require_permission,
    require_roles,
)

# Import modules that will be created
from app.core.security.roles import Permission, UserRole
from app.domain.schemas.auth_roles import RoleAssignment, UserAttributes


class TestUserRole:
    """Test user role enumeration and validation."""

    @pytest.mark.unit
    def test_user_role_enum_values(self):
        """Test that all expected user roles are defined."""
        expected_roles = ["admin", "trader", "fund_manager", "individual_investor"]

        for role_name in expected_roles:
            assert hasattr(UserRole, role_name.upper())
            role = getattr(UserRole, role_name.upper())
            assert role.value == role_name

    @pytest.mark.unit
    def test_user_role_validation(self):
        """Test that invalid roles are rejected."""
        with pytest.raises(ValueError):
            UserRole("invalid_role")


class TestPermission:
    """Test permission definitions and validation."""

    @pytest.mark.unit
    def test_permission_enum_values(self):
        """Test that all expected permissions are defined."""
        expected_permissions = [
            "wallet:read",
            "wallet:write",
            "wallet:delete",
            "portfolio:read",
            "portfolio:write",
            "defi:read",
            "defi:write",
            "admin:users",
            "admin:system",
        ]

        for perm_name in expected_permissions:
            assert hasattr(Permission, perm_name.upper().replace(":", "_"))

    @pytest.mark.unit
    def test_permission_validation(self):
        """Test that invalid permissions are rejected."""
        with pytest.raises(ValueError):
            Permission("invalid:permission")


class TestRoleAssignment:
    """Test role assignment schema validation."""

    @pytest.mark.unit
    def test_valid_role_assignment(self):
        """Test creating a valid role assignment."""
        assignment = RoleAssignment(
            user_id="user123",
            roles=["trader", "fund_manager"],
            attributes={"wallet_count": 5, "subscription_tier": "premium"},
        )

        assert assignment.user_id == "user123"
        assert "trader" in assignment.roles
        assert "fund_manager" in assignment.roles
        assert assignment.attributes["wallet_count"] == 5
        assert assignment.attributes["subscription_tier"] == "premium"

    @pytest.mark.unit
    def test_invalid_role_assignment(self):
        """Test that invalid roles are rejected in assignment."""
        with pytest.raises(ValueError):
            RoleAssignment(user_id="user123", roles=["invalid_role"], attributes={})


class TestUserAttributes:
    """Test user attributes schema validation."""

    @pytest.mark.unit
    def test_valid_user_attributes(self):
        """Test creating valid user attributes."""
        attributes = UserAttributes(
            wallet_count=3,
            portfolio_value=50000.0,
            subscription_tier="premium",
            defi_positions=["aave", "uniswap"],
        )

        assert attributes.wallet_count == 3
        assert attributes.portfolio_value == 50000.0
        assert attributes.subscription_tier == "premium"
        assert "aave" in attributes.defi_positions

    @pytest.mark.unit
    def test_optional_attributes(self):
        """Test that optional attributes can be omitted."""
        attributes = UserAttributes(wallet_count=1, portfolio_value=1000.0)

        assert attributes.wallet_count == 1
        assert attributes.portfolio_value == 1000.0
        assert attributes.subscription_tier is None
        assert attributes.defi_positions == []


class TestRequireRoles:
    """Test role-based access control dependencies."""

    @pytest.mark.unit
    def test_require_roles_success(self):
        """Test successful role check."""
        # Mock request with JWT payload containing required roles
        payload = {"roles": ["trader", "fund_manager"]}
        mock_request = Mock(state=Mock(token_payload=payload))

        # Create dependency
        role_dep = require_roles(["trader"])

        # Should not raise exception
        result = role_dep(mock_request)
        assert result == mock_request

    @pytest.mark.unit
    def test_require_roles_failure(self):
        """Test role check failure."""
        # Mock request with JWT payload without required roles
        payload = {"roles": ["individual_investor"]}
        mock_request = Mock(state=Mock(token_payload=payload))

        # Create dependency
        role_dep = require_roles(["admin", "trader"])

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            role_dep(mock_request)

        assert exc_info.value.status_code == 403
        assert "Access denied" in exc_info.value.detail

    @pytest.mark.unit
    def test_require_roles_multiple(self):
        """Test role check with multiple required roles (OR logic)."""
        # Mock request with JWT payload containing one of multiple required roles
        payload = {"roles": ["fund_manager"]}
        mock_request = Mock(state=Mock(token_payload=payload))

        # Create dependency
        role_dep = require_roles(["admin", "fund_manager", "trader"])

        # Should not raise exception (OR logic)
        result = role_dep(mock_request)
        assert result == mock_request


class TestRequireAttributes:
    """Test attribute-based access control dependencies."""

    @pytest.mark.unit
    def test_require_attributes_success(self):
        """Test successful attribute check."""
        # Mock request with JWT payload containing required attributes
        payload = {
            "attributes": {
                "geography": "US",
                "portfolio_value": 1000000,
                "kyc_level": "verified",
            }
        }
        mock_request = Mock(state=Mock(token_payload=payload))

        # Create dependency
        attr_dep = require_attributes(
            {"geography": "US", "portfolio_value": {"op": "gte", "value": 500000}}
        )

        # Should not raise exception
        result = attr_dep(mock_request)
        assert result == mock_request

    @pytest.mark.unit
    def test_require_attributes_failure(self):
        """Test attribute check failure."""
        # Mock request with JWT payload without required attributes
        payload = {"attributes": {"geography": "EU", "portfolio_value": 100000}}
        mock_request = Mock(state=Mock(token_payload=payload))

        # Create dependency
        attr_dep = require_attributes(
            {"geography": "US", "portfolio_value": {"op": "gte", "value": 500000}}
        )

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            attr_dep(mock_request)

        assert exc_info.value.status_code == 403
        assert "Access denied" in exc_info.value.detail

    @pytest.mark.unit
    def test_require_attributes_complex(self):
        """Test complex attribute requirements."""
        # Mock request with JWT payload containing various attributes
        payload = {
            "attributes": {
                "geography": "US",
                "portfolio_value": 2000000,
                "risk_tolerance": "high",
                "account_type": "institutional",
            }
        }
        mock_request = Mock(state=Mock(token_payload=payload))

        # Create dependency with complex requirements
        attr_dep = require_attributes(
            {
                "geography": {"op": "in", "value": ["US", "CA"]},
                "portfolio_value": {"op": "gt", "value": 1000000},
                "risk_tolerance": {"op": "neq", "value": "low"},
            }
        )

        # Should not raise exception
        result = attr_dep(mock_request)
        assert result == mock_request


class TestRequirePermission:
    """Test permission-based access control dependencies."""

    @pytest.mark.unit
    def test_require_permission_success(self):
        """Test successful permission check."""
        # Mock request with JWT payload containing trader role (has wallet:read permission)
        payload = {"roles": ["trader"]}
        mock_request = Mock(state=Mock(token_payload=payload))

        # Create dependency
        perm_dep = require_permission("wallet:read")

        # Should not raise exception
        result = perm_dep(mock_request)
        assert result == mock_request

    @pytest.mark.unit
    def test_require_permission_failure(self):
        """Test permission check failure."""
        # Mock request with JWT payload containing individual_investor role (no admin permissions)
        payload = {"roles": ["individual_investor"]}
        mock_request = Mock(state=Mock(token_payload=payload))

        # Create dependency
        perm_dep = require_permission("admin:users")

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            perm_dep(mock_request)

        assert exc_info.value.status_code == 403
        assert "Access denied" in exc_info.value.detail
