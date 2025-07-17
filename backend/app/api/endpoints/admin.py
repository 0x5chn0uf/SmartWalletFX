"""
Admin endpoints demonstrating RBAC/ABAC functionality.

This module showcases the Role-Based and Attribute-Based Access Control system
with different permission levels and attribute requirements.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.dependencies import (
    require_attributes,
    require_permission,
    require_roles,
)
from app.core.security.roles import Permission, UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository


class Admin:
    """Admin endpoint using singleton pattern with dependency injection."""

    ep = APIRouter(tags=["admin"])
    __user_repo: UserRepository

    def __init__(self, user_repository: UserRepository):
        """Initialize with injected dependencies."""
        Admin.__user_repo = user_repository

    @staticmethod
    @ep.get("/users", dependencies=[Depends(require_permission("admin:users"))])
    async def list_users():
        """List all users.
        Requires: admin:users permission (only ADMIN role has this)"""
        users = await Admin.__user_repo.get_all()
        return {
            "users": [
                {"id": str(u.id), "username": u.username, "email": u.email}
                for u in users
            ]
        }

    @staticmethod
    @ep.get("/analytics")
    async def get_analytics(
        current_user: User = Depends(require_roles(["admin", "fund_manager"]))
    ):
        """Get analytics data. Requires: ADMIN or FUND_MANAGER role (OR logic)"""
        return {
            "user_roles": getattr(current_user, "_current_roles", []),
            "analytics": {
                "total_portfolios": 150,
                "total_volume": 50000000,
                "active_traders": 89,
            },
        }

    @staticmethod
    @ep.get("/high-value-operations")
    async def high_value_operations(
        current_user: User = Depends(
            require_attributes(
                {
                    "portfolio_value": {"op": "gte", "value": 1000000},
                    "kyc_level": "verified",
                }
            )
        )
    ):
        """Access high-value operations.

        Requires: portfolio_value >= $1M AND kyc_level = "verified"
        """
        return {
            "user_attributes": getattr(current_user, "_current_attributes", {}),
            "operations": [
                {"type": "institutional_trading", "status": "available"},
                {"type": "large_block_trading", "status": "available"},
                {"type": "otc_trading", "status": "available"},
            ],
        }

    @staticmethod
    @ep.get("/regional-features")
    async def regional_features(
        current_user: User = Depends(
            require_attributes({"geography": {"op": "in", "value": ["US", "CA", "EU"]}})
        )
    ):
        """Access regional features. Requires: geography in ["US", "CA", "EU"]"""
        user_geography = getattr(current_user, "_current_attributes", {}).get(
            "geography", "unknown"
        )

        features = {
            "US": ["advanced_options", "crypto_futures", "margin_trading"],
            "CA": ["basic_options", "crypto_trading", "tfsa_accounts"],
            "EU": ["mifid_products", "crypto_trading", "regulated_investing"],
        }

        return {
            "geography": user_geography,
            "available_features": features.get(user_geography, ["basic_trading"]),
        }

    @ep.get("/system-health")
    async def get_system_health(
        current_user: User = Depends(require_permission("admin:system")),
    ):
        """Get system health information.

        Requires: admin:system permission (only ADMIN role has this)
        """
        return {
            "status": "healthy",
            "uptime": "99.9%",
            "services": {"database": "up", "redis": "up", "blockchain": "up"},
            "accessed_by": {
                "user_id": str(current_user.id),
                "roles": getattr(current_user, "_current_roles", []),
            },
        }

    @staticmethod
    @ep.post("/user-role", dependencies=[Depends(require_permission("admin:users"))])
    async def assign_user_role(
        user_id: str,
        role: str,
        current_user: User = Depends(require_permission("admin:users")),
    ):
        """Assign a role to a user.

        Requires: admin:users permission (only ADMIN role has this)
        """
        # Validate role
        try:
            UserRole(role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {role}. Valid roles: {[r.value for r in UserRole]}",  # noqa: E501
            )

        try:
            user = await Admin.__user_repo.get_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )

            # Update user roles
            current_roles = user.roles or []
            if role not in current_roles:
                current_roles.append(role)
                user.roles = current_roles
                await Admin.__user_repo.save(user)

            return {
                "message": f"Role {role} assigned to user {user.username}",
                "user_roles": current_roles,
                "assigned_by": str(current_user.id),
            }
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to assign role: {str(e)}",
            )

    @staticmethod
    @ep.get("/profile")
    async def get_user_profile(
        request: Request,
    ):
        """Get current user's profile with role and attribute information."""
        # Import here to avoid circular imports
        from app.api.dependencies import get_user_from_request

        current_user = await get_user_from_request(request)

        return {
            "user_id": str(current_user.id),
            "username": current_user.username,
            "email": current_user.email,
            "roles": getattr(
                current_user, "_current_roles", [UserRole.INDIVIDUAL_INVESTOR.value]
            ),
            "attributes": getattr(current_user, "_current_attributes", {}),
            "permissions": {
                "wallet": {
                    "read": "wallet:read"
                    in [
                        p.value
                        for role_name in getattr(current_user, "_current_roles", [])
                        for role in [UserRole(role_name)]
                        if role
                        in {UserRole.TRADER, UserRole.FUND_MANAGER, UserRole.ADMIN}
                        for p in [Permission.WALLET_READ]
                    ],
                    "write": "wallet:write"
                    in [
                        p.value
                        for role_name in getattr(current_user, "_current_roles", [])
                        for role in [UserRole(role_name)]
                        if role
                        in {UserRole.TRADER, UserRole.FUND_MANAGER, UserRole.ADMIN}
                        for p in [Permission.WALLET_WRITE]
                    ],
                }
            },
        }
