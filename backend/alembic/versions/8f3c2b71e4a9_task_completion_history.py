"""Add task completion history fields.

Revision ID: 8f3c2b71e4a9
Revises: 4d6ffdeb3a50
Create Date: 2026-06-14 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "8f3c2b71e4a9"
down_revision = "4d6ffdeb3a50"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("completed_by_id", sa.UUID(), nullable=True))
    op.add_column(
        "tasks",
        sa.Column(
            "completion_history",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.create_foreign_key(
        "fk_tasks_completed_by_id_users",
        "tasks",
        "users",
        ["completed_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.alter_column("tasks", "completion_history", server_default=None)


def downgrade() -> None:
    op.drop_constraint("fk_tasks_completed_by_id_users", "tasks", type_="foreignkey")
    op.drop_column("tasks", "completion_history")
    op.drop_column("tasks", "completed_by_id")

