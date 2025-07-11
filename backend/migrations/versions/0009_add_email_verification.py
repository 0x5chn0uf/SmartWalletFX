"""add email verification fields

Revision ID: 0009_add_email_verification
Revises: 0008_add_rbac_abac_fields
Create Date: 2025-07-03
"""

import sqlalchemy as sa
from alembic import op

revision = "0009_add_email_verification"
down_revision = "0008_add_rbac_abac_fields"
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
