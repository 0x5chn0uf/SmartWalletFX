import pytest

from app.core.security.roles import (
    Permission,
    UserRole,
    get_permissions_for_roles,
    has_all_roles,
    has_any_role,
    has_permission,
)
from app.schemas.auth_roles import Policy, RoleAssignment, UserAttributes


class TestRoleUtilityFunctions:
    def test_get_permissions_for_roles(self):
        perms = set(get_permissions_for_roles([UserRole.ADMIN.value]))
        # admin should include wallet:delete and admin:system
        assert Permission.WALLET_DELETE.value in perms
        assert Permission.ADMIN_SYSTEM.value in perms

    def test_get_permissions_for_roles_multiple(self):
        """Test getting permissions for multiple roles."""
        perms = set(
            get_permissions_for_roles(
                [UserRole.TRADER.value, UserRole.FUND_MANAGER.value]
            )
        )
        assert Permission.WALLET_READ.value in perms
        assert Permission.WALLET_WRITE.value in perms
        assert Permission.DEFI_READ.value in perms
        assert Permission.ADMIN_SYSTEM.value not in perms

    def test_get_permissions_for_roles_empty(self):
        """Test getting permissions for empty role list."""
        perms = get_permissions_for_roles([])
        assert perms == []

    def test_get_permissions_for_roles_invalid(self):
        """Test getting permissions for invalid role."""
        perms = get_permissions_for_roles(["invalid_role"])
        assert perms == []

    def test_has_permission_true(self):
        assert has_permission([UserRole.TRADER.value], Permission.WALLET_READ.value)

    def test_has_permission_false(self):
        assert not has_permission(
            [UserRole.INDIVIDUAL_INVESTOR.value], Permission.WALLET_DELETE.value
        )

    def test_has_permission_multiple_roles(self):
        """Test permission check with multiple roles."""
        assert has_permission(
            [UserRole.INDIVIDUAL_INVESTOR.value, UserRole.TRADER.value],
            Permission.WALLET_WRITE.value,
        )

    def test_has_permission_empty_roles(self):
        """Test permission check with empty role list."""
        assert not has_permission([], Permission.WALLET_READ.value)

    def test_has_permission_invalid_permission(self):
        """Test permission check with invalid permission."""
        assert not has_permission([UserRole.ADMIN.value], "invalid:permission")

    def test_has_any_role(self):
        assert has_any_role(
            [UserRole.ADMIN.value], [UserRole.ADMIN.value, UserRole.TRADER.value]
        )
        assert not has_any_role([], [UserRole.ADMIN.value])

    def test_has_any_role_multiple_matches(self):
        """Test has_any_role with multiple matching roles."""
        assert has_any_role(
            [UserRole.ADMIN.value, UserRole.TRADER.value],
            [UserRole.TRADER.value, UserRole.FUND_MANAGER.value],
        )

    def test_has_any_role_no_matches(self):
        """Test has_any_role with no matching roles."""
        assert not has_any_role(
            [UserRole.INDIVIDUAL_INVESTOR.value],
            [UserRole.ADMIN.value, UserRole.TRADER.value],
        )

    def test_has_all_roles(self):
        assert has_all_roles(
            [UserRole.ADMIN.value, UserRole.TRADER.value], [UserRole.ADMIN.value]
        )
        assert not has_all_roles(
            [UserRole.TRADER.value], [UserRole.TRADER.value, UserRole.ADMIN.value]
        )

    def test_has_all_roles_exact_match(self):
        """Test has_all_roles with exact role match."""
        assert has_all_roles(
            [UserRole.ADMIN.value, UserRole.TRADER.value],
            [UserRole.ADMIN.value, UserRole.TRADER.value],
        )

    def test_has_all_roles_empty_required(self):
        """Test has_all_roles with empty required roles."""
        assert has_all_roles([UserRole.ADMIN.value], [])

    def test_has_all_roles_empty_user_roles(self):
        """Test has_all_roles with empty user roles."""
        assert not has_all_roles([], [UserRole.ADMIN.value])


class TestUserRole:
    def test_get_default_role(self):
        """Test getting default role."""
        assert UserRole.get_default_role() == UserRole.INDIVIDUAL_INVESTOR.value

    def test_validate_role_valid(self):
        """Test validating valid roles."""
        assert UserRole.validate_role(UserRole.ADMIN.value)
        assert UserRole.validate_role(UserRole.TRADER.value)
        assert UserRole.validate_role(UserRole.FUND_MANAGER.value)
        assert UserRole.validate_role(UserRole.INDIVIDUAL_INVESTOR.value)

    def test_validate_role_invalid(self):
        """Test validating invalid role."""
        assert not UserRole.validate_role("invalid_role")
        assert not UserRole.validate_role("")


class TestPermission:
    def test_validate_permission_valid(self):
        """Test validating valid permissions."""
        assert Permission.validate_permission(Permission.WALLET_READ.value)
        assert Permission.validate_permission(Permission.ADMIN_SYSTEM.value)
        assert Permission.validate_permission(Permission.DEFI_WRITE.value)

    def test_validate_permission_invalid(self):
        """Test validating invalid permissions."""
        assert not Permission.validate_permission("invalid:permission")
        assert not Permission.validate_permission("")
        assert not Permission.validate_permission("wallet:invalid")


class TestUserAttributesValidation:
    def test_subscription_tier_validation(self):
        with pytest.raises(ValueError):
            UserAttributes(
                wallet_count=1, portfolio_value=100.0, subscription_tier="gold"
            )

    def test_defi_positions_validation(self):
        with pytest.raises(ValueError):
            UserAttributes(
                wallet_count=1,
                portfolio_value=100.0,
                defi_positions=["invalid_protocol"],
            )

    def test_valid_attributes(self):
        """Test creating valid user attributes."""
        attrs = UserAttributes(
            wallet_count=5,
            portfolio_value=1000.0,
            subscription_tier="premium",
            defi_positions=["aave", "compound"],
        )
        assert attrs.wallet_count == 5
        assert attrs.portfolio_value == 1000.0
        assert attrs.subscription_tier == "premium"
        assert "aave" in attrs.defi_positions
        assert "compound" in attrs.defi_positions


class TestRoleAssignmentValidation:
    def test_invalid_role_in_assignment(self):
        with pytest.raises(ValueError):
            RoleAssignment(user_id="u1", roles=["invalid"], attributes={})

    def test_invalid_attributes_in_assignment(self):
        # attributes with invalid subscription tier will bubble up
        with pytest.raises(ValueError):
            RoleAssignment(
                user_id="u1",
                roles=[UserRole.TRADER.value],
                attributes={"subscription_tier": "vip"},
            )

    def test_valid_role_assignment(self):
        """Test creating valid role assignment."""
        assignment = RoleAssignment(
            user_id="u1",
            roles=[UserRole.TRADER.value, UserRole.FUND_MANAGER.value],
            attributes={"subscription_tier": "premium"},
        )
        assert assignment.user_id == "u1"
        assert UserRole.TRADER.value in assignment.roles
        assert UserRole.FUND_MANAGER.value in assignment.roles
        assert assignment.attributes["subscription_tier"] == "premium"


class TestPolicyValidation:
    def test_invalid_operator(self):
        with pytest.raises(ValueError):
            Policy(name="p1", operator="XOR")

    def test_invalid_operator_type(self):
        with pytest.raises(ValueError):
            Policy(
                name="p1",
                operator="condition",
                operator_type="between",
                attribute="wallet_count",
                value=5,
            )

    def test_valid_policy(self):
        """Test creating valid policy."""
        policy = Policy(
            name="test_policy",
            operator="condition",
            operator_type="gte",
            attribute="wallet_count",
            value=5,
        )
        assert policy.name == "test_policy"
        assert policy.operator == "condition"
        assert policy.operator_type == "gte"
        assert policy.attribute == "wallet_count"
        assert policy.value == 5
