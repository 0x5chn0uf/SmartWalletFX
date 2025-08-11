"""add oauth accounts table"""

import sqlalchemy as sa
from alembic import op

revision = "0012_add_oauth_accounts_table"
down_revision = "0011_add_password_reset_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "oauth_accounts",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("provider_account_id", sa.String(length=128), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "provider", "provider_account_id", name="uq_oauth_provider_account"
        ),
    )
    op.create_index("ix_oauth_user_provider", "oauth_accounts", ["user_id", "provider"])


def downgrade() -> None:
    op.drop_index("ix_oauth_user_provider", table_name="oauth_accounts")
    op.drop_table("oauth_accounts")
