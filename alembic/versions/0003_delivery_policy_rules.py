"""add delivery policy rules table

Revision ID: 0003_delivery_policy_rules
Revises: 0002_notification_outbox
Create Date: 2026-05-08
"""

import sqlalchemy as sa

from alembic import op

revision = "0003_delivery_policy_rules"
down_revision = "0002_notification_outbox"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "delivery_policy_rules",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("scope", sa.String(length=16), nullable=False),
        sa.Column("scope_key", sa.String(length=128), nullable=False),
        sa.Column("channel", sa.String(length=32), nullable=True),
        sa.Column("priority", sa.String(length=16), nullable=True),
        sa.Column("rate_limit_per_minute", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_delivery_policy_rules_scope_scope_key",
        "delivery_policy_rules",
        ["scope", "scope_key"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_delivery_policy_rules_scope_scope_key", table_name="delivery_policy_rules")
    op.drop_table("delivery_policy_rules")
