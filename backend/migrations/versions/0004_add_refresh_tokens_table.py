"""add refresh tokens table

Revision ID: 0004_add_refresh_tokens_table
Revises: 0003_rename_password_hash_to_hashed_password
Create Date: 2025-06-18 11:03:26.742443

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004_add_refresh_tokens_table"
down_revision: Union[str, None] = "0003_rename_password_hash_to_hashed_password"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to add refresh_tokens table."""

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.UUID(), nullable=False, primary_key=True),
        sa.Column("jti_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column(
            "user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])


def downgrade() -> None:
    """Downgrade schema – drop refresh_tokens table."""

    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
