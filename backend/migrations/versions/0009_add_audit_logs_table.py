"""add audit_logs table

Revision ID: 0009_add_audit_logs_table
Revises: 0008_add_rbac_abac_fields
Create Date: 2025-07-02
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0009_add_audit_logs_table"
down_revision = "0008_add_rbac_abac_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:  # noqa: D401
    """Create audit_logs table and indexes."""

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(), nullable=False),
        sa.Column("operation", sa.String(length=20), nullable=False),
        sa.Column("user_id", postgresql.UUID(), nullable=False),
        sa.Column("changes", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
    )

    # Indexes for common query patterns
    op.create_index("idx_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("idx_audit_logs_user", "audit_logs", ["user_id"])
    op.create_index("idx_audit_logs_timestamp", "audit_logs", ["timestamp"])
    op.create_index("idx_audit_logs_operation", "audit_logs", ["operation"])
    op.create_index(
        "idx_audit_logs_changes_gin",
        "audit_logs",
        ["changes"],
        postgresql_using="gin",
    )


def downgrade() -> None:  # noqa: D401
    """Drop audit_logs table and indexes."""

    op.drop_index("idx_audit_logs_changes_gin", table_name="audit_logs")
    op.drop_index("idx_audit_logs_operation", table_name="audit_logs")
    op.drop_index("idx_audit_logs_timestamp", table_name="audit_logs")
    op.drop_index("idx_audit_logs_user", table_name="audit_logs")
    op.drop_index("idx_audit_logs_entity", table_name="audit_logs")
    op.drop_table("audit_logs")
