"""add aggregate_metrics table

Revision ID: 0006_add_aggregate_metrics_table
Revises: 0005_wallet_schema_updates
Create Date: 2025-06-24
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0006_add_aggregate_metrics_table"
down_revision = "0005_wallet_schema_updates"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "aggregate_metrics",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("wallet_id", sa.String(length=64), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tvl", sa.Float(), nullable=False),
        sa.Column("total_borrowings", sa.Float(), nullable=False),
        sa.Column("aggregate_apy", sa.Float(), nullable=True),
        sa.Column("positions", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_aggregate_metrics_wallet_id", "aggregate_metrics", ["wallet_id"]
    )


def downgrade():
    op.drop_index("ix_aggregate_metrics_wallet_id", table_name="aggregate_metrics")
    op.drop_table("aggregate_metrics")
