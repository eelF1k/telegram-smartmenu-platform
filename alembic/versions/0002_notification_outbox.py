"""add notification outbox table

Revision ID: 0002_notification_outbox
Revises: 0001_initial_schema
Create Date: 2026-05-08
"""

import sqlalchemy as sa

from alembic import op

revision = "0002_notification_outbox"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_outbox",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("dedupe_key", sa.String(length=255), nullable=False, unique=True),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("delivered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_notification_outbox_dedupe_key",
        "notification_outbox",
        ["dedupe_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_notification_outbox_dedupe_key", table_name="notification_outbox")
    op.drop_table("notification_outbox")
