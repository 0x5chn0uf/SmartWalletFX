"""
Pydantic schemas for RBAC/ABAC role and attribute management.

This module defines the data models for role assignments, user attributes,
and related authorization structures.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from app.core.security.roles import UserRole


class UserAttributes(BaseModel):
    """User attributes for attribute-based access control."""

    wallet_count: int = Field(
        default=0, ge=0, description="Number of wallets owned by user"
    )
    portfolio_value: float = Field(
        default=0.0, ge=0.0, description="Total portfolio value in USD"
    )
    subscription_tier: Optional[str] = Field(
        default=None, description="User subscription tier (basic, premium, enterprise)"
    )
    defi_positions: List[str] = Field(
        default_factory=list, description="List of DeFi protocols user has positions in"
    )

    @validator("subscription_tier")
    def validate_subscription_tier(cls, v):
        """Validate subscription tier values."""
        if v is not None and v not in ["basic", "premium", "enterprise"]:
            raise ValueError(
                "subscription_tier must be one of: basic, premium, enterprise"
            )
        return v

    @validator("defi_positions")
    def validate_defi_positions(cls, v):
        """Validate DeFi position protocol names."""
        valid_protocols = [
            "aave",
            "uniswap",
            "compound",
            "sushiswap",
            "curve",
            "balancer",
        ]
        for protocol in v:
            if protocol.lower() not in valid_protocols:
                raise ValueError(f"Invalid DeFi protocol: {protocol}")
        return [protocol.lower() for protocol in v]


class RoleAssignment(BaseModel):
    """Role assignment for a user."""

    user_id: str = Field(..., description="User ID")
    roles: List[str] = Field(default_factory=list, description="List of user roles")
    attributes: Dict[str, Any] = Field(
        default_factory=dict, description="User attributes for ABAC"
    )

    @validator("roles")
    def validate_roles(cls, v):
        """Validate that all roles are valid."""
        for role in v:
            if not UserRole.validate_role(role):
                raise ValueError(f"Invalid role: {role}")
        return v

    @validator("attributes")
    def validate_attributes(cls, v):
        """Validate user attributes structure."""
        # Convert to UserAttributes model for validation
        try:
            UserAttributes(**v)
        except Exception as e:
            raise ValueError(f"Invalid attributes: {e}")
        return v


class Policy(BaseModel):
    """Policy definition for attribute-based access control."""

    name: str = Field(..., description="Policy name")
    operator: str = Field(..., description="Policy operator (AND, OR, condition)")
    conditions: List["Policy"] = Field(
        default_factory=list, description="List of sub-policies for AND/OR operators"
    )
    attribute: Optional[str] = Field(
        default=None, description="Attribute name for condition evaluation"
    )
    operator_type: Optional[str] = Field(
        default=None, description="Operator type (eq, gt, lt, in, exists)"
    )
    value: Optional[Any] = Field(default=None, description="Value to compare against")

    @validator("operator")
    def validate_operator(cls, v):
        """Validate policy operator."""
        valid_operators = ["AND", "OR", "condition"]
        if v not in valid_operators:
            raise ValueError(f"Invalid operator: {v}. Must be one of {valid_operators}")
        return v

    @validator("operator_type")
    def validate_operator_type(cls, v):
        """Validate operator type for conditions."""
        if v is not None:
            valid_types = ["eq", "gt", "lt", "in", "exists"]
            if v not in valid_types:
                raise ValueError(
                    f"Invalid operator type: {v}. Must be one of {valid_types}"
                )
        return v


class AuthorizationRequest(BaseModel):
    """Request for authorization check."""

    user_id: str = Field(..., description="User ID")
    resource: str = Field(..., description="Resource being accessed")
    action: str = Field(..., description="Action being performed")
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Additional context for authorization"
    )


class AuthorizationResponse(BaseModel):
    """Response from authorization check."""

    allowed: bool = Field(..., description="Whether access is allowed")
    reason: Optional[str] = Field(
        default=None, description="Reason for authorization decision"
    )
    policies_applied: List[str] = Field(
        default_factory=list, description="List of policies that were evaluated"
    )


# Update forward references
Policy.model_rebuild()
