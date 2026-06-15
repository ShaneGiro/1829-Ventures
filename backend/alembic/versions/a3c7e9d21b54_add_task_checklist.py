"""Add checklist (sub-tasks / todos) to tasks.

Revision ID: a3c7e9d21b54
Revises: 9b1d4e2f6a73
Create Date: 2026-06-15 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "a3c7e9d21b54"
down_revision = "9b1d4e2f6a73"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column(
            "checklist",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("tasks", "checklist")
