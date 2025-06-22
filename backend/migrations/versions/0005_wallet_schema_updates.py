"""
wallet schema updates

Revision ID: 0005_wallet_schema_updates
Revises: 0004_add_refresh_tokens_table
Create Date: 2025-06-22 11:06:36.264470

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0005_wallet_schema_updates"
down_revision = "0004_add_refresh_tokens_table"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()

    # 1. Set wallet user_id non-nullable (skip for SQLite)
    if bind.dialect.name != "sqlite":
        op.alter_column("wallets", "user_id", existing_type=sa.UUID(), nullable=False)

    # 2. Update unique constraints on wallets table
    with op.batch_alter_table("wallets") as batch_op:
        # Drop previous unique index/constraint on address alone
        try:
            batch_op.drop_index("ix_wallets_address")
        except Exception:
            # If index name differs (e.g., auto-named on other dialects),
            # fallback to dropping by constraint name.
            try:
                batch_op.drop_constraint("wallets_address_key", type_="unique")
            except Exception:
                pass
        # Create new composite unique constraint
        batch_op.create_unique_constraint(
            "uq_wallet_user_address", ["user_id", "address"]
        )

        # 3. Make balance column nullable with default
        batch_op.alter_column(
            "balance",
            existing_type=sa.Numeric(precision=18, scale=8),
            nullable=True,
            server_default="0",
        )


def downgrade():
    bind = op.get_bind()

    with op.batch_alter_table("wallets") as batch_op:
        # 3. Revert balance column changes
        batch_op.alter_column(
            "balance",
            existing_type=sa.Numeric(precision=18, scale=8),
            nullable=False,
            server_default=None,
        )

        # 2. Revert unique constraints
        batch_op.drop_constraint("uq_wallet_user_address", type_="unique")
        batch_op.create_unique_constraint("wallets_address_key", ["address"])

    # 1. Revert user_id nullable (skip for SQLite)
    if bind.dialect.name != "sqlite":
        op.alter_column("wallets", "user_id", existing_type=sa.UUID(), nullable=True)
