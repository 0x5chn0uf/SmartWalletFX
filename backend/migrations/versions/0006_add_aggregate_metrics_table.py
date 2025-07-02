"""add aggregate_metrics table

Revision ID: 0006_add_aggregate_metrics_table
Revises: 0005_wallet_schema_updates
Create Date: 2024-03-19 10:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0006_add_aggregate_metrics_table"
down_revision = "0005_wallet_schema_updates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "aggregate_metrics",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("wallet_id", sa.UUID(), nullable=False),
        sa.Column("metric_type", sa.String(length=50), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
    )

    op.create_index(
        op.f("ix_aggregate_metrics_wallet_id"),
        "aggregate_metrics",
        ["wallet_id"],
        unique=False,
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_aggregate_metrics_wallet_id")
    op.drop_table("aggregate_metrics")
