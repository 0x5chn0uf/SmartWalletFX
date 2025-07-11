"""add email verification fields

Revision ID: 0013_add_email_verification
Revises: 0012_add_oauth_accounts_table
Create Date: 2025-07-03
"""

import sqlalchemy as sa
from alembic import op

revision = "0013_add_email_verification"
down_revision = "0012_add_oauth_accounts_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "email_verified", sa.Boolean(), nullable=False, server_default="false"
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("email_verified")
