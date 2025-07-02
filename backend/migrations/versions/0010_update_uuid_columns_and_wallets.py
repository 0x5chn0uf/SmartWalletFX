"""
update uuid columns and wallet schema using batch_alter_table for SQLite compatibility

Revision ID: fe32dc564e6a
Revises: 0009_add_audit_logs_table
Create Date: 2025-07-02 07:52:28.727529

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = "0010_update_uuid_columns_and_wallets"
down_revision = "0009_add_audit_logs_table"
branch_labels = None
depends_on = None


def upgrade():
    """Apply schema changes using batch_alter_table for better cross-dialect support."""
    # Aggregate metrics
    with op.batch_alter_table("aggregate_metrics") as batch_op:
        batch_op.alter_column(
            "id", existing_type=sa.NUMERIC(), type_=sa.UUID(), existing_nullable=False
        )

    # Audit logs
    with op.batch_alter_table("audit_logs") as batch_op:
        batch_op.alter_column(
            "id",
            existing_type=sa.BIGINT(),
            type_=sa.Integer(),
            existing_nullable=False,
            autoincrement=True,
        )
        batch_op.alter_column(
            "entity_id",
            existing_type=sa.NUMERIC(),
            type_=sa.String(length=36),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "user_id",
            existing_type=sa.NUMERIC(),
            type_=sa.String(length=36),
            existing_nullable=False,
        )

    # Recreate audit_logs indexes
    op.drop_index(op.f("idx_audit_logs_changes_gin"), table_name="audit_logs")
    op.drop_index(op.f("idx_audit_logs_entity"), table_name="audit_logs")
    op.drop_index(op.f("idx_audit_logs_operation"), table_name="audit_logs")
    op.drop_index(op.f("idx_audit_logs_timestamp"), table_name="audit_logs")
    op.drop_index(op.f("idx_audit_logs_user"), table_name="audit_logs")
    op.create_index(
        op.f("ix_audit_logs_entity_id"), "audit_logs", ["entity_id"], unique=False
    )
    op.create_index(
        op.f("ix_audit_logs_entity_type"), "audit_logs", ["entity_type"], unique=False
    )
    op.create_index(
        op.f("ix_audit_logs_operation"), "audit_logs", ["operation"], unique=False
    )
    op.create_index(
        op.f("ix_audit_logs_timestamp"), "audit_logs", ["timestamp"], unique=False
    )
    op.create_index(
        op.f("ix_audit_logs_user_id"), "audit_logs", ["user_id"], unique=False
    )

    # Groups
    with op.batch_alter_table("groups") as batch_op:
        batch_op.alter_column(
            "id", existing_type=sa.NUMERIC(), type_=sa.UUID(), existing_nullable=False
        )
        batch_op.alter_column(
            "user_id",
            existing_type=sa.NUMERIC(),
            type_=sa.UUID(),
            existing_nullable=True,
        )

    # Historical balances
    with op.batch_alter_table("historical_balances") as batch_op:
        batch_op.alter_column(
            "id", existing_type=sa.NUMERIC(), type_=sa.UUID(), existing_nullable=False
        )
        batch_op.alter_column(
            "wallet_id",
            existing_type=sa.NUMERIC(),
            type_=sa.UUID(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "token_id",
            existing_type=sa.NUMERIC(),
            type_=sa.UUID(),
            existing_nullable=True,
        )

    # Portfolio snapshot cache
    with op.batch_alter_table("portfolio_snapshot_cache") as batch_op:
        batch_op.alter_column(
            "id", existing_type=sa.NUMERIC(), type_=sa.UUID(), existing_nullable=False
        )

    # Portfolio snapshots
    with op.batch_alter_table("portfolio_snapshots") as batch_op:
        batch_op.alter_column(
            "id", existing_type=sa.NUMERIC(), type_=sa.UUID(), existing_nullable=False
        )

    # Refresh tokens
    with op.batch_alter_table("refresh_tokens") as batch_op:
        batch_op.alter_column(
            "id", existing_type=sa.NUMERIC(), type_=sa.UUID(), existing_nullable=False
        )
        batch_op.alter_column(
            "user_id",
            existing_type=sa.NUMERIC(),
            type_=sa.UUID(),
            existing_nullable=False,
        )
    op.add_column(
        "refresh_tokens",
        sa.Column("revoked", sa.Boolean(), server_default="false", nullable=False),
    )

    # Token balances
    with op.batch_alter_table("token_balances") as batch_op:
        batch_op.alter_column(
            "id", existing_type=sa.NUMERIC(), type_=sa.UUID(), existing_nullable=False
        )
        batch_op.alter_column(
            "wallet_id",
            existing_type=sa.NUMERIC(),
            type_=sa.UUID(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "token_id",
            existing_type=sa.NUMERIC(),
            type_=sa.UUID(),
            existing_nullable=True,
        )

    # Token prices
    with op.batch_alter_table("token_prices") as batch_op:
        batch_op.alter_column(
            "id", existing_type=sa.NUMERIC(), type_=sa.UUID(), existing_nullable=False
        )
        batch_op.alter_column(
            "token_id",
            existing_type=sa.NUMERIC(),
            type_=sa.UUID(),
            existing_nullable=True,
        )

    # Tokens
    with op.batch_alter_table("tokens") as batch_op:
        batch_op.alter_column(
            "id", existing_type=sa.NUMERIC(), type_=sa.UUID(), existing_nullable=False
        )

    # Transactions
    with op.batch_alter_table("transactions") as batch_op:
        batch_op.alter_column(
            "id", existing_type=sa.NUMERIC(), type_=sa.UUID(), existing_nullable=False
        )
        batch_op.alter_column(
            "wallet_id",
            existing_type=sa.NUMERIC(),
            type_=sa.UUID(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "token_id",
            existing_type=sa.NUMERIC(),
            type_=sa.UUID(),
            existing_nullable=True,
        )

    # Users
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "id", existing_type=sa.NUMERIC(), type_=sa.UUID(), existing_nullable=False
        )

    # Wallet groups
    with op.batch_alter_table("wallet_groups") as batch_op:
        batch_op.alter_column(
            "id", existing_type=sa.NUMERIC(), type_=sa.UUID(), existing_nullable=False
        )
        batch_op.alter_column(
            "wallet_id",
            existing_type=sa.NUMERIC(),
            type_=sa.UUID(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "group_id",
            existing_type=sa.NUMERIC(),
            type_=sa.UUID(),
            existing_nullable=True,
        )

    # Wallets
    with op.batch_alter_table("wallets") as batch_op:
        batch_op.alter_column(
            "id", existing_type=sa.NUMERIC(), type_=sa.UUID(), existing_nullable=False
        )
        batch_op.alter_column("address", existing_type=sa.VARCHAR(), nullable=False)
        batch_op.alter_column(
            "user_id", existing_type=sa.NUMERIC(), type_=sa.UUID(), nullable=False
        )
        batch_op.alter_column("is_active", existing_type=sa.BOOLEAN(), nullable=False)
        batch_op.alter_column(
            "balance_usd",
            existing_type=sa.NUMERIC(precision=18, scale=2),
            type_=sa.Float(),
            existing_nullable=True,
        )

    op.add_column("wallets", sa.Column("created_at", sa.DateTime(), nullable=False))
    op.add_column("wallets", sa.Column("updated_at", sa.DateTime(), nullable=False))
    op.drop_index(op.f("ix_wallets_id"), table_name="wallets")
    op.drop_index(op.f("ix_wallets_user_id"), table_name="wallets")
    op.create_index(op.f("ix_wallets_address"), "wallets", ["address"], unique=False)
    op.drop_column("wallets", "type")
    op.drop_column("wallets", "balance")
    op.drop_column("wallets", "extra_metadata")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("wallets", sa.Column("extra_metadata", sqlite.JSON(), nullable=True))
    op.add_column(
        "wallets",
        sa.Column(
            "balance",
            sa.NUMERIC(precision=18, scale=8),
            server_default=sa.text("'0'"),
            nullable=True,
        ),
    )
    op.add_column("wallets", sa.Column("type", sa.VARCHAR(), nullable=True))
    op.drop_index(op.f("ix_wallets_address"), table_name="wallets")
    op.create_index(op.f("ix_wallets_user_id"), "wallets", ["user_id"], unique=False)
    op.create_index(op.f("ix_wallets_id"), "wallets", ["id"], unique=False)
    op.alter_column(
        "wallets",
        "balance_usd",
        existing_type=sa.Float(),
        type_=sa.NUMERIC(precision=18, scale=2),
        existing_nullable=True,
    )
    op.alter_column("wallets", "is_active", existing_type=sa.BOOLEAN(), nullable=True)
    op.alter_column(
        "wallets", "user_id", existing_type=sa.UUID(), type_=sa.NUMERIC(), nullable=True
    )
    op.alter_column("wallets", "address", existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column(
        "wallets",
        "id",
        existing_type=sa.UUID(),
        type_=sa.NUMERIC(),
        existing_nullable=False,
    )
    op.drop_column("wallets", "updated_at")
    op.drop_column("wallets", "created_at")
    op.alter_column(
        "wallet_groups",
        "group_id",
        existing_type=sa.UUID(),
        type_=sa.NUMERIC(),
        nullable=False,
    )
    op.alter_column(
        "wallet_groups",
        "wallet_id",
        existing_type=sa.UUID(),
        type_=sa.NUMERIC(),
        nullable=False,
    )
    op.alter_column(
        "wallet_groups",
        "id",
        existing_type=sa.UUID(),
        type_=sa.NUMERIC(),
        existing_nullable=False,
    )
    op.alter_column(
        "users",
        "id",
        existing_type=sa.UUID(),
        type_=sa.NUMERIC(),
        existing_nullable=False,
    )
    op.alter_column(
        "transactions",
        "token_id",
        existing_type=sa.UUID(),
        type_=sa.NUMERIC(),
        existing_nullable=True,
    )
    op.alter_column(
        "transactions",
        "wallet_id",
        existing_type=sa.UUID(),
        type_=sa.NUMERIC(),
        existing_nullable=True,
    )
    op.alter_column(
        "transactions",
        "id",
        existing_type=sa.UUID(),
        type_=sa.NUMERIC(),
        existing_nullable=False,
    )
    op.alter_column(
        "tokens",
        "id",
        existing_type=sa.UUID(),
        type_=sa.NUMERIC(),
        existing_nullable=False,
    )
    op.alter_column(
        "token_prices",
        "token_id",
        existing_type=sa.UUID(),
        type_=sa.NUMERIC(),
        existing_nullable=True,
    )
    op.alter_column(
        "token_prices",
        "id",
        existing_type=sa.UUID(),
        type_=sa.NUMERIC(),
        existing_nullable=False,
    )
    op.alter_column(
        "token_balances",
        "token_id",
        existing_type=sa.UUID(),
        type_=sa.NUMERIC(),
        existing_nullable=True,
    )
    op.alter_column(
        "token_balances",
        "wallet_id",
        existing_type=sa.UUID(),
        type_=sa.NUMERIC(),
        existing_nullable=True,
    )
    op.alter_column(
        "token_balances",
        "id",
        existing_type=sa.UUID(),
        type_=sa.NUMERIC(),
        existing_nullable=False,
    )
    op.alter_column(
        "refresh_tokens",
        "user_id",
        existing_type=sa.UUID(),
        type_=sa.NUMERIC(),
        existing_nullable=False,
    )
    op.alter_column(
        "refresh_tokens",
        "id",
        existing_type=sa.UUID(),
        type_=sa.NUMERIC(),
        existing_nullable=False,
    )
    op.drop_column("refresh_tokens", "revoked")
    op.alter_column(
        "portfolio_snapshots",
        "id",
        existing_type=sa.UUID(),
        type_=sa.NUMERIC(),
        existing_nullable=False,
    )
    op.alter_column(
        "portfolio_snapshot_cache",
        "id",
        existing_type=sa.UUID(),
        type_=sa.NUMERIC(),
        existing_nullable=False,
    )
    op.alter_column(
        "historical_balances",
        "token_id",
        existing_type=sa.UUID(),
        type_=sa.NUMERIC(),
        existing_nullable=True,
    )
    op.alter_column(
        "historical_balances",
        "wallet_id",
        existing_type=sa.UUID(),
        type_=sa.NUMERIC(),
        existing_nullable=False,
    )
    op.alter_column(
        "historical_balances",
        "id",
        existing_type=sa.UUID(),
        type_=sa.NUMERIC(),
        existing_nullable=False,
    )
    op.alter_column(
        "groups",
        "user_id",
        existing_type=sa.UUID(),
        type_=sa.NUMERIC(),
        existing_nullable=True,
    )
    op.alter_column(
        "groups",
        "id",
        existing_type=sa.UUID(),
        type_=sa.NUMERIC(),
        existing_nullable=False,
    )
    op.drop_index(op.f("ix_audit_logs_user_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_timestamp"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_operation"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_entity_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_entity_id"), table_name="audit_logs")
    op.create_index(
        op.f("idx_audit_logs_user"), "audit_logs", ["user_id"], unique=False
    )
    op.create_index(
        op.f("idx_audit_logs_timestamp"), "audit_logs", ["timestamp"], unique=False
    )
    op.create_index(
        op.f("idx_audit_logs_operation"), "audit_logs", ["operation"], unique=False
    )
    op.create_index(
        op.f("idx_audit_logs_entity"),
        "audit_logs",
        ["entity_type", "entity_id"],
        unique=False,
    )
    op.create_index(
        op.f("idx_audit_logs_changes_gin"), "audit_logs", ["changes"], unique=False
    )
    op.alter_column(
        "audit_logs",
        "user_id",
        existing_type=sa.String(length=36),
        type_=sa.NUMERIC(),
        existing_nullable=False,
    )
    op.alter_column(
        "audit_logs",
        "entity_id",
        existing_type=sa.String(length=36),
        type_=sa.NUMERIC(),
        existing_nullable=False,
    )
    op.alter_column(
        "audit_logs",
        "id",
        existing_type=sa.Integer(),
        type_=sa.BIGINT(),
        existing_nullable=False,
        autoincrement=True,
    )
    op.alter_column(
        "aggregate_metrics",
        "id",
        existing_type=sa.UUID(),
        type_=sa.NUMERIC(),
        existing_nullable=False,
    )
    # ### end Alembic commands ###
