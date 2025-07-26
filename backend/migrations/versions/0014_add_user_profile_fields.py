"""
add user profile fields

Revision ID: 0014_add_user_profile_fields
Revises: 0013_email_verification_tokens
Create Date: 2025-07-23 09:01:30.310724

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0014_add_user_profile_fields"
down_revision = "0013_email_verification_tokens"
branch_labels = None
depends_on = None


def upgrade():
    # Add profile management fields to users table
    op.add_column(
        "users", sa.Column("profile_picture_url", sa.String(length=500), nullable=True)
    )
    op.add_column(
        "users", sa.Column("first_name", sa.String(length=100), nullable=True)
    )
    op.add_column("users", sa.Column("last_name", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("bio", sa.String(length=1000), nullable=True))
    op.add_column("users", sa.Column("timezone", sa.String(length=50), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "preferred_currency",
            sa.String(length=10),
            nullable=True,
            server_default="USD",
        ),
    )
    op.add_column(
        "users", sa.Column("notification_preferences", sa.JSON(), nullable=True)
    )


def downgrade():
    # Remove profile management fields from users table
    op.drop_column("users", "notification_preferences")
    op.drop_column("users", "preferred_currency")
    op.drop_column("users", "timezone")
    op.drop_column("users", "bio")
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
    op.drop_column("users", "profile_picture_url")
