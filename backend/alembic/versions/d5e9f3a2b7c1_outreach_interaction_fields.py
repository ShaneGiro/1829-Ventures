"""Add outreach workflow fields to interactions.

Revision ID: d5e9f3a2b7c1
Revises: c4d8e2f1a6b9
Create Date: 2026-07-10 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "d5e9f3a2b7c1"
down_revision = "c4d8e2f1a6b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("interactions", sa.Column("channel", sa.String(length=32), nullable=True))
    op.add_column(
        "interactions",
        sa.Column("direction", sa.String(length=16), server_default="internal", nullable=False),
    )
    op.add_column(
        "interactions",
        sa.Column("follow_up_status", sa.String(length=16), server_default="none", nullable=False),
    )
    op.add_column(
        "interactions",
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    for column in ("channel", "direction", "follow_up_status", "created_by_id"):
        op.create_index(f"ix_interactions_{column}", "interactions", [column], unique=False)


def downgrade() -> None:
    for column in ("created_by_id", "follow_up_status", "direction", "channel"):
        op.drop_index(f"ix_interactions_{column}", table_name="interactions")
        op.drop_column("interactions", column)
