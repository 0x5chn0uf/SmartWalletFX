"""add email verification fields

Revision ID: 0011_add_email_verification_fields
Revises: 0010_update_uuid_columns
Create Date: 2025-07-03
"""

import sqlalchemy as sa
from alembic import op

revision = "0011_add_email_verification_fields"
down_revision = "0010_update_uuid_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "email_verified", sa.Boolean(), nullable=False, server_default="false"
            )
        )
        batch_op.add_column(
            sa.Column(
                "verification_deadline", sa.DateTime(timezone=True), nullable=True
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("verification_deadline")
        batch_op.drop_column("email_verified")
