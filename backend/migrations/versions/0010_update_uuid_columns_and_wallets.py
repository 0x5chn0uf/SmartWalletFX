"""
update uuid columns and wallet schema using batch_alter_table

Revision ID: 0010_update_uuid_columns
Revises: 0009_add_email_verification
Create Date: 2024-03-19 10:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0010_update_uuid_columns"
down_revision = "0009_add_email_verification"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new wallet columns only (is_active already exists from 0001_init)
    with op.batch_alter_table("wallets", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("last_sync_timestamp", sa.DateTime(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("sync_status", sa.String(length=20), nullable=True)
        )
        batch_op.add_column(sa.Column("sync_error", sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove only the new columns
    with op.batch_alter_table("wallets", schema=None) as batch_op:
        batch_op.drop_column("sync_error")
        batch_op.drop_column("sync_status")
        batch_op.drop_column("last_sync_timestamp")
