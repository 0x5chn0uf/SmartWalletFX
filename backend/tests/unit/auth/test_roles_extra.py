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

    def test_has_permission_true(self):
        assert has_permission([UserRole.TRADER.value], Permission.WALLET_READ.value)

    def test_has_permission_false(self):
        assert not has_permission(
            [UserRole.INDIVIDUAL_INVESTOR.value], Permission.WALLET_DELETE.value
        )

    def test_has_any_role(self):
        assert has_any_role(
            [UserRole.ADMIN.value], [UserRole.ADMIN.value, UserRole.TRADER.value]
        )
        assert not has_any_role([], [UserRole.ADMIN.value])

    def test_has_all_roles(self):
        assert has_all_roles(
            [UserRole.ADMIN.value, UserRole.TRADER.value], [UserRole.ADMIN.value]
        )
        assert not has_all_roles(
            [UserRole.TRADER.value], [UserRole.TRADER.value, UserRole.ADMIN.value]
        )


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
