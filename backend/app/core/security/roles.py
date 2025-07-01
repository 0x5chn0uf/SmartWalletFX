"""
Role-based and attribute-based access control (RBAC/ABAC) definitions.

This module defines the core role and permission enums used throughout the
authorization system.
"""

from enum import Enum
from typing import Dict, List


class UserRole(str, Enum):
    """User roles for role-based access control."""

    ADMIN = "admin"
    TRADER = "trader"
    FUND_MANAGER = "fund_manager"
    INDIVIDUAL_INVESTOR = "individual_investor"

    @classmethod
    def get_default_role(cls) -> str:
        """Get the default role for backward compatibility."""
        return cls.INDIVIDUAL_INVESTOR.value

    @classmethod
    def validate_role(cls, role: str) -> bool:
        """Validate if a role string is valid."""
        try:
            cls(role)
            return True
        except ValueError:
            return False


class Permission(str, Enum):
    """Permissions for fine-grained access control."""

    # Wallet permissions
    WALLET_READ = "wallet:read"
    WALLET_WRITE = "wallet:write"
    WALLET_DELETE = "wallet:delete"

    # Portfolio permissions
    PORTFOLIO_READ = "portfolio:read"
    PORTFOLIO_WRITE = "portfolio:write"

    # DeFi permissions
    DEFI_READ = "defi:read"
    DEFI_WRITE = "defi:write"

    # Admin permissions
    ADMIN_USERS = "admin:users"
    ADMIN_SYSTEM = "admin:system"

    @classmethod
    def validate_permission(cls, permission: str) -> bool:
        """Validate if a permission string is valid."""
        try:
            cls(permission)
            return True
        except ValueError:
            return False


# Role to permission mappings
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    UserRole.ADMIN.value: [
        Permission.WALLET_READ.value,
        Permission.WALLET_WRITE.value,
        Permission.WALLET_DELETE.value,
        Permission.PORTFOLIO_READ.value,
        Permission.PORTFOLIO_WRITE.value,
        Permission.DEFI_READ.value,
        Permission.DEFI_WRITE.value,
        Permission.ADMIN_USERS.value,
        Permission.ADMIN_SYSTEM.value,
    ],
    UserRole.TRADER.value: [
        Permission.WALLET_READ.value,
        Permission.WALLET_WRITE.value,
        Permission.PORTFOLIO_READ.value,
        Permission.PORTFOLIO_WRITE.value,
        Permission.DEFI_READ.value,
        Permission.DEFI_WRITE.value,
    ],
    UserRole.FUND_MANAGER.value: [
        Permission.WALLET_READ.value,
        Permission.WALLET_WRITE.value,
        Permission.PORTFOLIO_READ.value,
        Permission.PORTFOLIO_WRITE.value,
        Permission.DEFI_READ.value,
        Permission.DEFI_WRITE.value,
    ],
    UserRole.INDIVIDUAL_INVESTOR.value: [
        Permission.WALLET_READ.value,
        Permission.PORTFOLIO_READ.value,
        Permission.DEFI_READ.value,
    ],
}


def get_permissions_for_roles(roles: List[str]) -> List[str]:
    """Get all permissions for a list of roles."""
    permissions = set()

    for role in roles:
        if role in ROLE_PERMISSIONS:
            permissions.update(ROLE_PERMISSIONS[role])

    return list(permissions)


def has_permission(user_roles: List[str], required_permission: str) -> bool:
    """Check if user has a specific permission based on their roles."""
    user_permissions = get_permissions_for_roles(user_roles)
    return required_permission in user_permissions


def has_any_role(user_roles: List[str], required_roles: List[str]) -> bool:
    """Check if user has any of the required roles."""
    if not user_roles:
        return False

    return any(role in user_roles for role in required_roles)


def has_all_roles(user_roles: List[str], required_roles: List[str]) -> bool:
    """Check if user has all of the required roles."""
    if not user_roles:
        return False

    return all(role in user_roles for role in required_roles)


# Backwards-compat alias expected by older modules/tests
ROLE_PERMISSIONS_MAP = ROLE_PERMISSIONS
