"""Rename users.password_hash to hashed_password

Revision ID: 0003_hashed_password
Revises: 0002_add_portfolio_snapshot_cache_table
Create Date: 2025-06-17 12:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa  # noqa: F401 — required by Alembic for context
from alembic import op

# revision identifiers, used by Alembic.
revision = "0003_hashed_password"
down_revision = "0002_snapshot_cache_table"
branch_labels = None
depends_on = None


def upgrade() -> None:  # noqa: D401
    """Apply the migration."""
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column("password_hash", new_column_name="hashed_password")


def downgrade() -> None:  # noqa: D401
    """Revert the migration."""
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column("hashed_password", new_column_name="password_hash")
