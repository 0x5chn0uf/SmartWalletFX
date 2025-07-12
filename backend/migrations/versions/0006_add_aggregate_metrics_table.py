"""add aggregate_metrics table

Revision ID: 0006_add_aggregate_metrics_table
Revises: 0005_wallet_schema_updates
Create Date: 2024-03-19 10:00:00.000000

"""
import sqlalchemy as sa  # noqa: F401
from alembic import op  # noqa: F401

# revision identifiers, used by Alembic.
revision = "0006_add_aggregate_metrics_table"
down_revision = "0005_wallet_schema_updates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
