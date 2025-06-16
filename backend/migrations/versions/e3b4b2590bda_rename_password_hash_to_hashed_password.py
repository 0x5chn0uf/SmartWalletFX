from __future__ import annotations

"""Rename users.password_hash to hashed_password

Revision ID: e3b4b2590bda
Revises: 62719eef5af2
Create Date: 2025-06-17 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "e3b4b2590bda"
down_revision = "62719eef5af2"
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